#!/usr/bin/env python

import argparse
import codecs
import os
import shutil
import sys

import appscript

from omnigraffle_export.omnigraffle_command import OmniGraffleSandboxedCommand

from data_model import Canvas

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



#. TRANSLATORS: Please leave %s as it is, because it is needed by the program.

""" 

class OmniGraffle6Translator(OmniGraffleSandboxedCommand):
    """Translator for OmniGraffle6"""
    
    def translate(self):
        self.open_document()
        memory = {}
        for canvas in self.doc.canvases():
            c = Canvas(canvas)
            c.walk(os.path.basename(self.args.source), canvas.name(), memory)
        # close window and restore settings
        self.og.windows.first().close()

        rev_memory = { memory[key] : key for key in memory.keys() }

        with codecs.open("%s.pot" % self.args.target, 'w+', 'utf-8') as target:

            target.write("#. TRANSLATORS: Please keep \\n (linebreaks) and \\\" (quotes).\n")
            target.write("#. Thank you for contributing to this project.\n\n")

            for key in rev_memory.keys():
                target.write(key)
                value = rev_memory[key].replace("\n", '\\n')
                value = value.replace("\"", '\\\"')
                target.write("msgid \"%s\"\n" % value)
                target.write("msgstr \"%s\"\n\n" % value)


    def parse_commandline(self):
        """Parse commandline, do some checks and return args."""

        parser = self.get_parser()
        return parser.parse_args()

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                         description="Translate canvases in OmniGraffle 6.",
                                         epilog="If a file fails, simply try again.")

        parser.add_argument('source', type=str,
                            help='an OmniGraffle file')
        parser.add_argument('target', type=str,
                            help='fname of file with texts')

        parser.add_argument('--canvas', type=str,
                            help='translate canvas with given name')

        parser.add_argument('--verbose', '-v', action='count')

        return parser


def main():
    translator = OmniGraffle6Translator()
    translator.translate()


if __name__ == '__main__':
    main()
