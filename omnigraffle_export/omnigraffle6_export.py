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
Planned extensions:


* add defaults for scale (1.0) and resolution (1.94444441795)
* add option for html image type: jpg, png, tiff
* find out why HTML and SVG export is not working
* export all files in a folder

File naming:
------------

1. Single Canvas Export:
    * target filename has proper format extension: export to that filename (create dirs along the way)
    * target filename has no extension: create folder if necessary, and export to "Canvas Name" in that folder

2. Multipage File:
    * target filename has proper format extencion: export to that filename (create dirs along the way)
    * target filename has no extension: create folder if necessary, and export to source.basename + extension in that folder

3. Multi Canvas Export:
    * treat target as folder, create one file per canvas inside
"""


class OmniGraffle6Exporter(object):

    """Exporter for OmniGraffle6"""

    SANDBOXED_DIR = '~/Library/Containers/com.omnigroup.OmniGraffle%s/Data/'

    EXPORT_FORMATS = [
        'bmp',
        'eps',
        'gif',
        # 'html' TODO: NOT WORKING (OSERROR -50 "The document cannot be exported to the "HTML text" format."
        'jpg',
        'png',
        'pdf',
        'psd',  # Photoshop
        # 'svg' TODO: NOT WORKING (OSERROR -50 "The document cannot be exported to the "scalable vector graphics (SVG)" format.")
        'tiff',
        'vdx',  # Visio XML
    ]
    MULTIPAGE_FORMATS = ('pdf', 'vdx')

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
        self.args.format = self.args.format.lower()

        if self.args.format not in self.EXPORT_FORMATS:
            ArgumentParser.error(
                "format '%s' not supported." % self.args.format)
            sys.exit(1)        

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

        self.backup_current_export_settings()
        self.open_document()
        self.set_export_settings()

        # removes trailing slash, if present!
        target = os.path.abspath(self.args.target)

        def _split_filename(fn, frmt):
            """Return (directory, filenname) if extension matches frmt, (directory, '') otherwise."""
            ext = os.path.splitext(target)[1]
            if not ext or ext[1:].lower() != frmt:
                return fn, ''
            else:
                return os.path.split(fn)

        if self.args.format in self.MULTIPAGE_FORMATS:
            # 1. Multipart Format: export to '<target> if filename, else to
            # <target>/<source-filename>.<format>'

            directory, fname = _split_filename(target, self.args.format)
            if not fname:

                dummy, fname = os.path.split(self.args.source)
                fname = "%s.%s" % (
                    os.path.splitext(fname)[0], self.args.format)
            self.export_file(self.args.format, directory, fname)

        elif self.args.canvas:
            # 2. Single Canvas: export to '<target> if filename, else to
            # <target>/<canvas-name>.<format>'
            directory, fname = _split_filename(target, self.args.format)
            if not fname:
                fname = "%s.%s" % (self.args.canvas, self.args.format)
            self.export_canvas(
                self.args.format, directory, fname, self.args.canvas)

        elif len(self.doc.canvases()) == 1:
            # 3. Only one canvas in file: xport to
            # '<target>/<canvas-name>.<format>'
            c = self.doc.canvases()[0]
            canvas_name = c.name()
            fname = "%s.%s" % (canvas_name, self.args.format)
            self.export_canvas(self.args.format, target, fname, canvas_name)

        else:
            # 4. File with multiple canvases: export to '<target>'
            self.export_dir(self.args.format, target)

        # close window and restore settings
        self.og.windows.first().close()
        self.restore_saved_export_settings()

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
            export_path = os.path.join(self.get_sandbox_path(), fname)
            # self._clear(export_path) TODO: is this even necessary

        self._og_export(export_format, export_path)

        if self.sandboxed():
            # move back out of sandbox
            if not os.path.exists(directory):
                os.makedirs(directory)
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
            export_path = os.path.join(self.get_sandbox_path(), os.path.basename(directory))
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

    SETTINGS_TO_BACKUP = (
        'area_type',
        'border_amount',
        'draws_background',
        'export_scale',
        #'html_image_type', TODO: html image type can't be None - find out when this happens and how to avoid
        'include_border',
        'origin',
        'resolution',
        'size',
        )

    def backup_current_export_settings(self):
        """Save current export settings so we can restore afterwards."""
        for setting in self.SETTINGS_TO_BACKUP:
            # value = self.og.current_export_settings.area_type()
            self.settings_backup[setting] = getattr(self.og.current_export_settings, setting)()
        
        if self.args.verbose:
            # display current export settings
            for k, v in self.settings_backup.items():
                print k, v

    def restore_saved_export_settings(self):
        for setting in self.SETTINGS_TO_BACKUP:    
            # self.og.current_export_settings.area_type.set(value)
            getattr(self.og.current_export_settings, setting).set(self.settings_backup[setting])

    def set_export_settings(self):
        if self.args.transparent:
            self.og.current_export_settings.draws_background.set(False)
        else:
            self.og.current_export_settings.draws_background.set(True)
        if self.args.resolution:
            self.og.current_export_settings.resolution.set(
                self.args.resolution)
        if self.args.scale:
            self.og.current_export_settings.export_scale.set(self.args.scale)

        # will be overridden in export_canvas() for canvas export
        self.og.current_export_settings.area_type.set(
            appscript.k.entire_document)

    def parse_commandline(self):
        """Parse commandline, do some checks and return args."""

        parser = self.get_parser()
        return parser.parse_args()

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                         description="Export canvases from OmniGraffle 6.",
                                         epilog=dedent("""
            If a file fails, simply try again. 

            Export uses current export settings stored in OmniGraffle for each filetype, except for those 
            explicity overridden through arguments. Overridden export settings are restored to previous 
            values in OmniGraffle after export.

            Arguments can be read from a file, filename needs to be prefixed with @ on the commandline. In
            config files, use one argument per line (e.g. --resolution=1.0).

            """))

        parser.add_argument('format', type=str,
                            help="Export formats: bmp, eps, gif, jpg, png, pdf, psd (Photoshop), tiff, vdx (Visio XML) (not supported: html, svg)")

        parser.add_argument('source', type=str,
                            help='an OmniGraffle file')
        parser.add_argument('target', type=str,
                            help='folder to export to')

        parser.add_argument('--canvas', type=str,
                            help='export canvas with given name')
        parser.add_argument('--scale', type=float,
                            help=' The scale to use during export (1.0 is 100%%)')
        parser.add_argument('--resolution', type=float,
                            help='The number of pixels per point in the resulting exported image (1.0 for 72 DPI)')
        parser.add_argument('--transparent', dest='transparent', action='store_true',
                            help='export with transparent background')

        parser.add_argument('--verbose', '-v', action='count')

        return parser


def main():

    exporter = OmniGraffle6Exporter()
    exporter.export()


if __name__ == '__main__':
    main()
