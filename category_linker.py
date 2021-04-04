# todo: replace this ad hoc solution with entity linker
from product_category_loader import ngram_index
from product_category_loader import _stop_words
from product_category_loader import _normalize





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

def link_categories(text):
    return _link(text, ngram_index)


