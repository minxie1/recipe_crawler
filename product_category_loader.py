import pandas as pd
import ast


def load_categories(category_file):
    records = pd.read_csv(category_file).dropna()
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

def index_categories_ngrams(categories):
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


def index_categories_full_name(categories):
    index = {}
    for category_products in categories:
        category = _normalize(category_products["name"])
        if category not in index:
            index[category] = [category_products]
        else:
            index[category].append(category_products)

    return index

_stop_words = {
    'a',
    'an',
    'the'
}

category_file = "data/product_categories.csv"
categories = load_categories(category_file)
full_name_index = index_categories_full_name(categories)
ngram_index = index_categories_ngrams(categories)