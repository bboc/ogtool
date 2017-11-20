#!/usr/bin/env python

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
        except (appscript.ApplicationNotFoundError):
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

        print 'opening', fname

        self.og.activate()

        # adhoc fix for https://github.com/fikovnik/omnigraffle-export/issues/23
        # apparently the process is sandboxed and cannot access the file
        # 16/03/2015 13:01:54.000 kernel[0]: Sandbox: OmniGraffle(66840) deny file-read-data test.graffle
        # therefore we first try to open it manually

        import subprocess
        subprocess.call(['open', fname])

        # window = self.og.windows.first()
        # doc = window.document()
        self.doc = self.og.open(fname)

        logging.debug('Opened OmniGraffle file: ' + fname)

    def open_copy_of_document_(self, filename, suffix):
        """create and open a copy of an omnigraffle document."""
        root, ext = os.path.splitext(filename)
        doc_copy = root + '-' + suffix + ext
        shutil.copyfile(filename, doc_copy)
        self.open_document(doc_copy)

    def open_copy_of_document(self, source, target=None, suffix=None):
        """
        Create and open a copy of an omnigraffle document.
        Target takes precedence over sufix, if target is given and is a directory, the target
        file name will be created from target and the basename of source. If target is ommited,
        but suffix is given, the target filename will be created by extending source with suffix.
        """
        if target:
            if os.path.isdir(target):
                # create full target file name from basenam of source file
                target = os.path.join(target, os.path.basename(source))
        if suffix and not target:
            root, ext = os.path.splitext(source)
            target = root + '-' + suffix + ext
        print "copy:", source, target
        shutil.copyfile(source, target)
        self.open_document(target)

    def parse_commandline(self):
        """Parse commandline, do some checks and return args."""

        parser = self.get_parser()
        args = parser.parse_args()
        # set up loglevel
        logging.basicConfig(level=args.loglevel)
        return args

    @staticmethod
    def add_verbose(parser):
        parser.add_argument(
            '-d', '--debug',
            help="print debug output",
            action="store_const", dest="loglevel", const=logging.DEBUG,
            default=logging.WARNING
        )
        parser.add_argument(
            '-v', '--verbose',
            help="more detailed output",
            action="store_const", dest="loglevel", const=logging.INFO,
        )
