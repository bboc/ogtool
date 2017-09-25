"""
Example plugin for ogtools: dump all text from a document.

To run:

$ ogtool run-plugin extract_text ./tests/color-test.graffle --noconfig --canvas my-canvas -vvv
"""

import codecs

from omnigraffle.data_model import Canvas, Named


def main(document, config, canvas=None):

    with codecs.open(document.name() + ".txt", 'w+', 'utf-8') as fp:

        def dump_text(element):
            text = element.text
            if text:
                fp.write(text)
                fp.write('\n')
            if isinstance(element, Named) and element.name:
                fp.write(element.name)
                fp.write('\n')

        def dump_canvas(c):
            cv = Canvas(c)
            fp.write("\n\n-------------------------------\n")
            fp.write(cv.name)
            fp.write("\n-------------------------------\n\n")
            cv.walk(dump_text)

        if canvas:
            dump_canvas(canvas)
        else:
            for c in document.canvases():
                dump_canvas(c)
