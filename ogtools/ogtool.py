#!/usr/bin/env python

import argparse
import codecs
from collections import defaultdict
from functools import partial
import os
import shutil
import sys

import appscript
import polib


from omnigraffle.command import OmniGraffleSandboxedCommand

from omnigraffle.data_model import Canvas, TextContainer

"""
Translation of Omnigrafle files

1. Create Translation memory
    - get all cavases in file
    - for each canvas: get all text objects and dump to pot-file

2. Update translatiosn
    - create a copy of OmniGraffle source file language suffix
    - read po-file and make a translation dictionary d[msgid] = msgstr
        (replace newlines and quotes!!)
    - walk through all objects, if text: replace with translated text
    - save

TODO: how to make sure OmniGraffle files are not changed between exporting pot and tranlsation? 
    Create dedicated image repo (needs branchens for each resource release) or add to the repo
     where illustrations are used (adds lots of duplication)

Do we need keys and template files?

    - create a key (hash) for each text
    - create a omnigraffle template file where texts are replaced by hashes
    - copy templates and fill in translations template files

""" 

class OmniGraffleSandboxedTools(OmniGraffleSandboxedCommand):
    """Some tools for OmniGraffle 6+"""

    def cmd_dump_colors_and_fonts(self):
        """
        Dump a list of all used colors and fonts.
        """

        self.open_document()
        colors = set()
        fonts = set()
        def extract(colors, fonts, element):
            pass
        for canvas in self.doc.canvases():
            c = Canvas(canvas)
            c.walk(partial(extract, colors, fonts))
            # TODO: must also use invisible layers!!!

        self.og.windows.first().close()



    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                         description="Manipulate some stuff in omnigraffle documents.",
                                         epilog="If a file fails, simply try again.")

        subparsers = parser.add_subparsers()
        OmniGraffleSandboxedTools.add_parser_dump(subparsers)
        parser.add_argument('--verbose', '-v', action='count')
        return parser

    @staticmethod
    def add_parser_dump(subparsers):
        sp = subparsers.add_parser('dump',
                                   help="Dump a list of all colors and fonts in an Omnigraffle document.")
        sp.add_argument('source', type=str,
                            help='an OmniGraffle file')
        sp.add_argument('--canvas', type=str,
                            help='select a canvas with given name')
        sp.set_defaults(func=OmniGraffleSandboxedTools.cmd_dump_colors_and_fonts)


def main():
    ogtool = OmniGraffleSandboxedTools()
    ogtools.args.func(ogtool)


if __name__ == '__main__':
    main()
