#!/usr/bin/env python

import argparse
import logging
import os
import shutil


import appscript

class OmniGraffleSandboxedCommand(object):

    SANDBOXED_DIR = '~/Library/Containers/com.omnigroup.OmniGraffle%s/Data/'

    def __init__(self, args=None):
        """Read args from commandline if not present, and connect to OmniGraffle app."""
        if args:
            self.args = args
        else:
            self.args = self.parse_commandline()

        self._check_args()
        self.doc = None
        self.settings_backup = {}
        try:
            self.og = appscript.app('OmniGraffle')
        except (ApplicationNotFoundError):
            raise RuntimeError('Unable to connect to OmniGraffle 6 ')

    def _check_args(self):
    	"""Hook to validate commandline arguments."""
    	pass


    def sandboxed(self):
        # real check using '/usr/bin/codesign --display --entitlements - /Applications/OmniGraffle.app'
        return self.og.version()[0] >= '6'
        # before: return self.og.version()[0] == '6' and os.path.exists(os.path.expanduser(self.SANDBOXED_DIR))


    def get_sandbox_path(self):
        version = self.og.version()[0]
        path = os.path.expanduser(self.SANDBOXED_DIR % version)

        if not os.path.exists(path):
            raise RuntimeError('OmniGraffle is sandboxed but missing sandbox path: %s' % path)

        return path

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

        if self.args.verbose:
            print 'opening', fname

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

    def open_copy_of_document(self, filename, suffix):
        """create and open a copy of an omnigraffle document."""
        root, ext = os.path.splitext(filename)
        doc_copy = root + '-' + suffix + ext
        shutil.copyfile(filename, doc_copy)
        self.open_document(doc_copy)


    def parse_commandline(self):
        """Parse commandline, do some checks and return args."""

        parser = self.get_parser()
        return parser.parse_args()

