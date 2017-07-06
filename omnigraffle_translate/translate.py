#!/usr/bin/env python

import argparse
import codecs
import logging
import os
import shutil
import sys
import tempfile

from textwrap import dedent
import appscript

from data_model import Canvas

"""
Translation of Omnigrafle files

1. Create Translation memory
    - get all cavases in file
    - for each canvas: get all text objects and dump to file

2. Update translatiosn
    - make a copy of each OG file with language suffix
    - go through all canvases and objects and replace text
    - export all canvases?


Do we need keys and template files?

    - create a key (hash) for each text
    - create a omnigraffle template file where texts are replaced by hashes
    - copy templates and fill in translations template files



#. TRANSLATORS: Please leave %s as it is, because it is needed by the program.
#. Thank you for contributing to this project.
#: src/name.c:36
msgid "My name is %s.\n"
msgstr ""

""" 



class OmniGraffle6Translator(object):
    """Translator for OmniGraffle6"""

    SANDBOXED_DIR_6 = '~/Library/Containers/com.omnigroup.OmniGraffle6/Data/'


    def __init__(self, args=None):
        """Read args from commandline if not present, and connect to OmniGraffle app."""
        if args:
            self.args = args
        else:
            self.args = self.parse_commandline()

        self.doc = None
        self.settings_backup = {}
        try:
            self.og = appscript.app('OmniGraffle')
        except (ApplicationNotFoundError):
            raise RuntimeError('Unable to connect to OmniGraffle 6 ')

    def sandboxed(self):
        # real check using '/usr/bin/codesign --display --entitlements -
        # /Applications/OmniGraffle.app'
        return self.og.version()[0] == '6' and os.path.exists(os.path.expanduser(self.SANDBOXED_DIR_6))

    def get_canvas_list(self):
        """Return a list of names of all the canvases in the document."""
        return [c.name() for c in self.doc.canvases()]

    def open_document(self, fname=None):
        if not fname:
            fname = self.args.source

        fname = os.path.abspath(fname)
        if not os.path.isfile(fname) and \
                not os.path.isfile(os.path.join(fname, "data.plist")):
            raise ValueError('File: %s does not exists' % fname)

        fname = os.path.abspath(fname)
        self.og.activate()

        # adhoc fix for https://github.com/fikovnik/omnigraffle-export/issues/23
        # apparently the process is sandboxed and cannot access the file
        # 16/03/2015 13:01:54.000 kernel[0]: Sandbox: OmniGraffle(66840) deny file-read-data test.graffle
        # therefore we first try to open it manually

        import subprocess
        subprocess.call(['open', fname])

        window = self.og.windows.first()
        # doc = window.document()
        self.doc = self.og.open(fname)

        logging.debug('Opened OmniGraffle file: ' + fname)

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
