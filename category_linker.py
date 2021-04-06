
import pandas as pd
import ast
import numpy as np
from nltk import ngrams
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction import FeatureHasher

import boto3
from urllib.parse import urlparse
import tempfile
import pickle
import os

strick_match = os.environ.get('STRICT_MATCH', True)

# todo: remove unused functions, and packages

def download(remote_path):
    temp_filepath = next(tempfile._get_candidate_names())

    with open(temp_filepath, 'wb') as f:
        o = urlparse(remote_path)
        bucket = o.netloc
        key = o.path.lstrip('/')
        s3 = boto3.client('s3')
        s3.download_fileobj(bucket, key, f)

    return temp_filepath


def read_obj(remote_path):
    temp_filepath = download(remote_path)

    with open(temp_filepath, 'rb') as f:
        obj = pickle.load(f)

    os.remove(temp_filepath)
    return obj


class NLP_NLTK(object):
    def __init__(self, **kwargs):
        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        from nltk.stem import PorterStemmer

        nltk.download('stopwords')
        nltk.download('punkt')

        stop_words = set(stopwords.words('english'))
        porter = PorterStemmer()
        self._nlp = (stop_words, porter, word_tokenize)

    def to_normalized_tokens(self, text):
        tokens = self._nlp[2](text)
        return [self._nlp[1].stem(w) for w in tokens if not w in self._nlp[0]]


def get_ngrams(tokens, n):
    return set(
        ' '.join(ngram) for ngram in
        ngrams(tokens, n, pad_left=True, left_pad_symbol='<s>', pad_right=True, right_pad_symbol='</s>')
    )


def get_features(tokens, mention, entity_id, **kwargs):
    # tokens are the tokenized text generated by a pre-process
    # ngram of 'token B_token I_token' sequence
    tokens_with_mention_tag = list(tokens)
    tokens_with_mention_tag[mention[0]] = 'B_' + tokens_with_mention_tag[mention[0]]
    for i in range(mention[0] + 1, mention[1] + 1):
        tokens_with_mention_tag[i] = 'I_' + tokens_with_mention_tag[i]
    # todo: configurable to use which n-grams to use
    ngrams = get_ngrams(tokens_with_mention_tag, 2)

    return {
        **{
            'entity_id': entity_id,
            # entity features
            'mention_coverage_ratio': (mention[1] - mention[0] + 1) / len(tokens),
        },
        # mention tag ngrams
        **{
            'mention_tag_bigram_' + ngram: 1 for ngram in ngrams
        },
        **kwargs,
    }


class EntityRanker(object):
    def __init__(self, **kwargs):
        self._feature_weights = None
        self._model = None

    @classmethod
    def load_from_dict(cls, **dict):
        self = cls()
        self._model = LogisticRegression(solver='saga', random_state=0)
        for name, p in dict.pop('model').items():
            setattr(self._model, name, np.array(p))

        self._feature_hasher = FeatureHasher(n_features=dict.pop('n_features'), alternate_sign=False)

        return self

    def predict(self, query, mention_entity_id_pairs):
        features_list = []
        tokens = query.split(' ')
        for mention, entity_id in mention_entity_id_pairs:
            features = get_features(tokens, mention, entity_id)
            features_list.append(features)

        X = self._feature_hasher.transform(features_list)

        # note: not using self._model.predict(X), which returns the predicted label
        # use sparse matrix dot as the rank score
        # incase we need a prob, call self._model.predict_proba(X)[:,1]

        return X.dot(self._model.coef_[0])


def _load_categories():
    records = pd.read_csv('product_categories.csv').dropna()
    records.astype({'PRODUCT_CATEGORY_ID': 'int32'})
    categories = []
    for r in records.to_dict(orient='records'):
        id = r['PRODUCT_CATEGORY_ID']
        name = r['PRODUCT_CATEGORY']
        products = r['PRODUCTS']
        categories.append(
            {
                'id': id,
                'name': name,
                'products': ast.literal_eval(products) if products else []
            }
        )
    return categories


_nlp = NLP_NLTK()


def _normalize(text):
    return ' '.join(_nlp.to_normalized_tokens(text))

with open('ranker_model_small.pickle', 'rb') as f:
    ranker_model = pickle.load(f)

# ranker_model = read_obj('s3://instacart-lore/development/entity_linking/ranker_model.pickle')

_ranker = EntityRanker.load_from_dict(**ranker_model)


def _index_categories(categories):
    index = {}
    for c in categories:
        name = c['name']
        normalized_name = _normalize(name)
        # category name index
        if strick_match:
            e = normalized_name
            items = index.get(e, [])
            if c not in items:
                items.append(c)
            index[e] = items
            continue
        # n-gram index
        name_tokens = normalized_name.split()
        total = len(name_tokens)
        for n in range(1, total + 1):
            for i in range(total - n + 1):
                e = ' '.join(name_tokens[i: i + n])
                items = index.get(e, [])
                if c not in items:
                    items.append(c)
                index[e] = items
    return index


def _rank(normalized_text, mention_entity_pairs):
    mention_entity_id_pairs = [(mention, 'CATEGORY:' + str(int(entity['id']))) for mention, entity in
                               mention_entity_pairs]
    rank_scores = _ranker.predict(normalized_text, mention_entity_id_pairs)
    so = np.argsort(rank_scores)
    mention_entity_pairs = list(np.array(mention_entity_pairs)[so])
    rank_scores = list(np.array(rank_scores)[so])
    mention_entity_pairs.reverse()
    rank_scores.reverse()
    return mention_entity_pairs, rank_scores


def _link(text, index):
    normalized_text = _normalize(text)
    tokens = normalized_text.split()
    total = len(tokens)
    # match all n-gram
    for n in range(total, 0, -1):
        mention_entity_pairs = []
        for i in range(total - n + 1):
            start = i
            end = i + n - 1
            e = ' '.join(tokens[start: end + 1])
            items = index.get(e, None)
            if items:
                for item in items:
                    mention = (start, end)
                    mention_entity_pairs.append((mention, item))
        # do we have ngram match?
        if mention_entity_pairs:
            ranked_mention_entity_pairs, rank_scores = _rank(normalized_text, mention_entity_pairs)
            # return all pairs or just top 1?
            if rank_scores[0] > 0:
                return [ranked_mention_entity_pairs[0][1]]

    return None


_categories = _load_categories()
_index = _index_categories(_categories)


def link_categories(text):
    return _link(text, _index)


# print(link_categories('onion'))
