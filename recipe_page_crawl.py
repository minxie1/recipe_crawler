import argparse
import requests
from bs4 import BeautifulSoup



def recipe_page_crawl(url):
    try:
        page = requests.get(url)
    except:
        print("url crawling failed!")
        return []
    try:
        results = BeautifulSoup(page.content, 'html.parser')
    except:
        print("webpage parsing failed!")
        return []

    ret = []
    ingredient_elems = results.find_all('span', class_='ingredients-item-name')
    for ingredient_elem in ingredient_elems:
        ingredient = ingredient_elem.text.strip()
        ret.append(ingredient)
        # print(ingredient)
    return ret


def main():
    url = 'https://www.allrecipes.com/recipe/264440/traditional-spaghetti-allamatriciana/'
    recipe_page_crawl(url)


if __name__ == "__main__":
    main()