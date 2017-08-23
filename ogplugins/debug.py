"""
Example plugin for ogtools: drop into debugger in each canvas

To run:

$ ogtool run-plugin debug --noconfig ./tests/color-test.graffle
"""

import pdb


from omnigraffle.data_model import Document, Canvas, Layer


def main(document, config, canvas=None, verbose=None):

    def debug(element):
        if isinstance(element, Canvas) or isinstance(element, Layer):
            print element.item_info()
            pdb.set_trace()

    d = Document(document)
    d.walk(debug)
