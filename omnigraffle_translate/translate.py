#!/usr/bin/env python

import argparse
import logging
import os
import shutil
import sys
import tempfile

from textwrap import dedent
import appscript

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

    def export(self):

    
        self.open_document()

        #import pdb; pdb.set_trace()
        for canvas in self.doc.canvases():

            print(repr(canvas.name()))
            for layer in canvas.layers():
                print(layer.name())
                for solid in layer.solids():
                    try: 
                        id = solid.id()
                    except appscript.reference.CommandError:
                        id = None
                    try: 
                        text = solid.text()
                    except appscript.reference.CommandError:
                        text = None
                    print(id, text)


        # close window and restore settings
        self.og.windows.first().close()

    def export_canvas(self, export_format, directory, fname, canvas):
        """Export a single canvas."""
        self.og.current_export_settings.area_type.set(
            appscript.k.current_canvas)
        for c in self.doc.canvases():
            if c.name() == canvas:
                self.og.windows.first().canvas.set(c)
                self.export_file(export_format, directory, fname)
                return
        else:
            print "ERROR: canvas '%s' not found in document. List of existing canvases: \n%s" % (canvas, '\n'.join(self.get_canvas_list()))
            self.restore_saved_export_settings()
            sys.exit(1)

    @staticmethod
    def _clear(path):
        """Remove file or directory."""
        if os.path.exists(path):
            if os.path.isfile(path):
                os.unlink(path)
            else:
                shutil.rmtree(path)

    def _og_export(self, export_format, export_path):
        self.doc.save(as_=export_format, in_=export_path)

    def export_file(self, export_format, directory, fname):
        """Export to a single file."""
        export_path = os.path.join(directory, fname)

        if self.sandboxed():
            # export to sandbox
            export_path = os.path.join(
                os.path.expanduser(self.SANDBOXED_DIR_6), fname)
            # self._clear(export_path) TODO: is this even necessary

        self._og_export(export_format, export_path)

        if self.sandboxed():
            # move back out of sandbox
            if not os.path.exists(directory):
                os.makedirs(directory)
            self._clear(directory)
            os.rename(export_path, os.path.join(directory, fname))

    def export_dir(self, export_format, directory):
        """
        Export contents of a file to a directory. Sometimes OmniGraffle automatically adds 
        an extension to the target directory, so both cases need to be handled.

        TODO: test when exactly this happens and simplify code
        """

        export_path = directory

        if self.sandboxed():
            # export to sandbox
            export_path = os.path.expanduser(
                self.SANDBOXED_DIR_6) + os.path.basename(directory)
            export_path_with_extension = "%s.%s" % (export_path, export_format)

        self._og_export(export_format, export_path)

        if self.sandboxed():
            # make dirs if necessary
            root = os.path.split(directory)[0]
            if not os.path.exists(root):
                os.makedirs(root)
            # move back out o tssandbox
            self._clear(directory)
            if os.path.exists(export_path_with_extension):
                os.rename(export_path_with_extension, directory)
            else:
                os.rename(export_path, directory)

    def parse_commandline(self):
        """Parse commandline, do some checks and return args."""

        parser = self.get_parser()
        return parser.parse_args()

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                         description="Translate canvases in OmniGraffle 6.",
                                         epilog=dedent("""
            If a file fails, simply try again. 
            """))

        parser.add_argument('source', type=str,
                            help='an OmniGraffle file')
        parser.add_argument('target', type=str,
                            help='fname of file with texts')

        parser.add_argument('--canvas', type=str,
                            help='export canvas with given name')

        parser.add_argument('--verbose', '-v', action='count')

        return parser


def main():

    print('foo')
    exporter = OmniGraffle6Translator()
    exporter.export()


if __name__ == '__main__':
    main()
