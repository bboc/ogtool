"""
Example plugin for ogtools: print a list of all nodes in a document.

To run:

$ ogtool run-plugin list_nodes ./tests/color-test.graffle  --noconfig --canvas my-canvas -vvv
"""

from functools import partial
from collections import defaultdict

import appscript

from omnigraffle.data_model import Document


def main(document, config, canvas=None):

    def list_nodes(nodes, element):
        if element.text:
            print element.text
        try:
            element.item.id()
        except appscript.reference.CommandError:
            return  # some elements (e.g. Document) have no id
        print element.info, element.__class__
        nodes['%s (%s)' % (element.item.id(), element.__class__)] += 1
        ids[element.item.id()] += 1

    nodes = defaultdict(int)
    ids = defaultdict(int)
    d = Document(document)
    d.walk(partial(list_nodes, nodes))

    for i in sorted(ids.keys()):
        print i, ids[i]
