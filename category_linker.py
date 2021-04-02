# todo: replace this ad hoc solution with entity linker
import pandas as pd
import ast


def _load_categories():
    records = pd.read_csv('categories_v2.csv').dropna()
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


def _normalize(text):
    return ' '.join(text.lower().split())


_stop_words = {
    'a',
    'an',
    'the'
}


def _index_categories(categories):
    index = {}
    for c in categories:
        name = c['name']
        normalized_name = _normalize(name)
        name_tokens = normalized_name.split()
        total = len(name_tokens)
        # index all ngrams
        for n in range(1, total + 1):
            for i in range(total - n + 1):
                e = ' '.join(name_tokens[i: i + n])
                # if e is stop words
                if e in _stop_words:
                    continue
                items = index.get(e, [])
                if c not in items:
                    items.append(c)
                index[e] = items
    return index


def _link(text, index):
    normalized_text = _normalize(text)
    tokens = normalized_text.split()
    total = len(tokens)
    # match all n-gram
    for n in range(total, 0, -1):
        for i in range(total - n + 1):
            e = ' '.join(tokens[i: i + n])
            if e in _stop_words:
                continue
            items = index.get(e, None)
            if items:
                return items
    return None


_categories = _load_categories()
_index = _index_categories(_categories)


def link_categories(text):
    return _link(text, _index)


