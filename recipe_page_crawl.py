import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

def clean_ingredient(ingredient):
    replacements = {"¼": "0.25", "½": "0.5", "⅔": "0.67"}
    return "".join([replacements.get(c, c) for c in ingredient])

# extraction patten for each site
def recipe_page_crawl_allrecipes(parsed_page):
    ret = []
    ingredient_elems = parsed_page.find_all('span', class_='ingredients-item-name')
    for ingredient_elem in ingredient_elems:
        ingredient = ingredient_elem.text.strip()
        ret.append(clean_ingredient(ingredient))
    # print(ret)
    return ret


def recipe_page_crawl_womanandhome(parsed_page):
    ret = []
    ul_elems = parsed_page.find_all('ul', class_='recipe-ingredient-list')
    for ul_elem in ul_elems:
        ingredient_elems = ul_elem.find_all('li')
        for ingredient_elem in ingredient_elems:
            ingredient = ingredient_elem.text.strip()
            ret.append(clean_ingredient(ingredient))
    # print(ret)
    return ret


def recipe_page_crawl_deliciousmagazine(parsed_page):
    ret = []
    div_elems = parsed_page.find_all('div', class_='recipe-ingredients text-standard')
    for div_elem in div_elems:
        ingredient_elems = div_elem.find_all('li')
        for ingredient_elem in ingredient_elems:
            ingredient = ingredient_elem.text.strip()
            ret.append(clean_ingredient(ingredient))
    # print(ret)
    return ret


domain_to_func = {
    "www.allrecipes.com": recipe_page_crawl_allrecipes,
    "www.womanandhome.com": recipe_page_crawl_womanandhome,
    "www.deliciousmagazine.co.uk": recipe_page_crawl_deliciousmagazine
}


def recipe_page_crawl(url):
    try:
        page = requests.get(url)
    except:
        print("url crawling failed!")
        return []
    try:
        parsed_page = BeautifulSoup(page.content, 'html.parser')
    except:
        print("webpage parsing failed!")
        return []

    domain = urlparse(url).netloc
    if domain not in domain_to_func: return []

    return domain_to_func[domain](parsed_page)


def main():
    # url = 'https://www.allrecipes.com/recipe/264440/traditional-spaghetti-allamatriciana/'
    # url = 'https://www.womanandhome.com/recipes/sesame-prawn-and-noodle-salad-recipe/'
    url = 'https://www.deliciousmagazine.co.uk/recipes/spelt-chicory-mushroom-one-pot/'
    recipe_page_crawl(url)


if __name__ == "__main__":
    main()