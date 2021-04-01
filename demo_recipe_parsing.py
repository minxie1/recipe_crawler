import gradio as gr
import json
import subprocess
import tempfile
import utils
import category_linker

from recipe_page_crawl import recipe_page_crawl


def _exec_crf_test(input_text, model_path):
    with tempfile.NamedTemporaryFile(mode='w') as input_file:
        input_file.write(utils.export_data(input_text))
        input_file.flush()
        return subprocess.check_output(
            ['crf_test', '--verbose=1', '--model', model_path,
             input_file.name]).decode('utf-8')


def _convert_crf_output_to_dict(crf_output):
    return utils.parse_crf_output(crf_output)


def _link_ingredient_to_categories(ingredient):
    return category_linker.link_categories(ingredient['name'])

def recipe_parse(url):
    if not url: return "Url is empty!", ""
    ingredients = recipe_page_crawl(url)
    if ingredients:
        model_file = "20210330_2040-nyt-ingredients-snapshot-2015-49381ad.crfmodel"
        crf_output = _exec_crf_test(ingredients, model_file)
        results = _convert_crf_output_to_dict(crf_output.split('\n'))
        # remove result
        results = [r for r in results if r]
        # remove comment, other
        for r in results:
            r.pop('comment', None)
            r.pop('other', None)
            # join tokens
            for k in r:
                r[k] = ' '.join(r[k])
        # link categories and products
        for r in results:
            categories = _link_ingredient_to_categories(r)
            r['linked_categories'] = categories

        return "\n".join(ingredients), json.dumps(results, indent=2)
    else:
        return "Couldn't get ingredients from page!", ""


iface = gr.Interface(fn=recipe_parse, inputs="text", outputs=["text", "text"], css="styles.css")
iface.launch()
