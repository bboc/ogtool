"""
Example plugin for ogtools: print a list of all nodes in a document.

To run:

$ ogtool run-plugin list_nodes ./tests/color-test.graffle  ogplugins/example_plugin.yaml --canvas my-canvas -vvv
"""

from functools import partial
from collections import defaultdict

from omnigraffle.data_model import Document


def main(document, config, canvas=None, verbose=None):

    def list_nodes(nodes, element):
        if not isinstance(element, Document):
            # print element.item.id(), element.item.class_(), element.__class__
            nodes['%s (%s)' % (element.item.id(), element.__class__)] += 1
            ids[element.item.id()] += 1
        else:
            pass  # documents have no id!

    nodes = defaultdict(int)
    ids = defaultdict(int)
    d = Document(document)
    d.walk(partial(list_nodes, nodes))

    for i in sorted(ids.keys()):
        print i
