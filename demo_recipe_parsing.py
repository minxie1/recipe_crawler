import gradio as gr
import json
import subprocess
import tempfile
import utils

from recipe_page_crawl import recipe_page_crawl

def _exec_crf_test(input_text, model_path):
    with tempfile.NamedTemporaryFile(mode='w') as input_file:
        input_file.write(utils.export_data(input_text))
        input_file.flush()
        return subprocess.check_output(
            ['crf_test', '--verbose=1', '--model', model_path,
             input_file.name]).decode('utf-8')


def _convert_crf_output_to_json(crf_output):
    return json.dumps(utils.import_data(crf_output), indent=2, sort_keys=True)


def recipe_parse(url):
    if not url: return "", ""
    ingredients = recipe_page_crawl(url)
    model_file = "20210330_2040-nyt-ingredients-snapshot-2015-49381ad.crfmodel"
    crf_output = _exec_crf_test(ingredients, model_file)
    # print(_convert_crf_output_to_json(crf_output.split('\n')))

    return "\n".join(ingredients), _convert_crf_output_to_json(crf_output.split('\n'))


iface = gr.Interface(fn=recipe_parse, inputs="text", outputs=["text", "text"], css="styles.css")
iface.launch()