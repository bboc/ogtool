#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example plugin for ogtools: drop into debugger in each canvas

To run:

$ ogtool run-plugin debug --noconfig ./tests/color-test.graffle
"""

import pdb


from omnigraffle.data_model import Document, Canvas, Layer


def main(document, config, canvas=None):

    def debug(element):
        if isinstance(element, Canvas) or isinstance(element, Layer):
            # note: since this is normal plugin output,
            # it does NOT go to logging.debug!
            print element.info
            pdb.set_trace()

    d = Document(document)
    d.walk(debug)
