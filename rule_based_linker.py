import numpy as np
import sys
from product_category_loader import full_name_index
from product_category_loader import _normalize
PRODUCT_CATEGORY_NOT_FIND = -1



def _get_edit_distance(str_1, str_2):
    len_1 = len(str_1)
    len_2 = len(str_2)

    partial_dist = np.zeros((len_1 + 1, len_2 + 1), dtype=int)
    for i in range(0, len_1 + 1):
        for j in range(0, len_2 + 1):
            if i == 0:
                partial_dist[i][j] = j
            elif j == 0:
                partial_dist[i][j] = i
            elif str_1[i - 1] == str_2[j - 1]:
                partial_dist[i][j] = partial_dist[i - 1][j - 1]
            else:
                partial_dist[i][j] = 1 + min(partial_dist[i - 1][j], partial_dist[i][j - 1], partial_dist[i - 1][j - 1])

    return partial_dist[len_1][len_2]

def _find_partial_matching(ingredient, edit_distance_threshold):

    partial_mapping_result = ""
    min_edit_dist = sys.maxsize
    for product_category in full_name_index:
        if ingredient in product_category or product_category in ingredient:
            cur_edit_dist = _get_edit_distance(ingredient, product_category)
            if cur_edit_dist < min_edit_dist:
                min_edit_dist = cur_edit_dist
                partial_mapping_result = product_category

    # if the edit distance in the partial is equal or larger than the threshold,
    # then we do not trust the partial match results and we will let the ngram liker to handle it.
    if min_edit_dist < edit_distance_threshold:
        return partial_mapping_result, min_edit_dist
    else:
        return "", min_edit_dist

def _preprocessing(ingredient):
    # normailze the ingredient term,
    # if there is "or" in the term, e.g., "A or B",
    # we will use "B" to find a match

    token_list = _normalize(ingredient).split()
    for idx, token in enumerate(token_list):
        if token == "or":
            return " ".join(token_list[idx+1:])
    return _normalize(ingredient)

def map_ingredients_to_categories(ingredient, edit_dist_threshold):

    ingredient = _preprocessing(ingredient)
    mapped_product_category_name = ""
    # check if there is an exact match
    if ingredient in full_name_index:
        mapped_product_category_name = ingredient

    # if not, check for partial match
    else:
        mapped_product_category_name, min_edit_distance = _find_partial_matching(ingredient, edit_dist_threshold)

    products_info = None
    if len(mapped_product_category_name) > 0:
        products_info = full_name_index[mapped_product_category_name]

    return mapped_product_category_name, products_info
