"""
Combine yaml and html output from several runs of ogtool dump into.

Usage:

$ og-tool run-plugin example_plugin ./tests/color-test.graffle  ogplugins/example_plugin.yaml --canvas my-canvas -vvv


create collect.yaml:
    ls -b *.yaml
    prefix each line with '- ' in sublime text
    remove crowding.yaml etc.
$ ogtool run-plugin combine_colors_and_fonts dummy.graffle collect.yaml
"""

import glob
import yaml

from omnigraffle.data_model import Document
from ogtools.colors import hexcolors, dump_colors_and_fonts_to_yaml_and_html, color_components


def main(document, config, canvas=None, verbose=None):
    fonts = dict(all=set())
    colors = set()

    for item in config:
        stream = open(item, "r")
        config = yaml.load(stream)
        if config['fonts']:
            for f in config['fonts'].keys():
                fonts['all'].add(f)
        for c in config['colors'].keys():
            colors.add(color_components(c))

    result = {
        'fonts': sorted([f for f in fonts['all']]),
        'colors': sorted([c for c in colors]),
    }
    with open('combined.yaml', 'w+') as target:
        target.write(yaml.dump(result, encoding='utf-8'))

    dump_colors_and_fonts_to_yaml_and_html('combined.xxx', colors, fonts)
