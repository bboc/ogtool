#!/usr/bin/env python

import argparse
import logging
import os
import shutil
import sys
import tempfile

from textwrap import dedent
import appscript


class OmniGraffle6Exporter(object):
    """Exporter for OmniGraffle6"""

    SANDBOXED_DIR_6 = '~/Library/Containers/com.omnigroup.OmniGraffle6/Data/'
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

        self.backup_current_export_settings()
        self.open_document()
        self.set_export_settings()

        target = os.path.abspath(self.args.target)

        if self.args.canvas:
            self.export_canvas(target, self.args.format, self.args.canvas)
        else:
            self.export_item(target, self.args.format)

        self.og.windows.first().close()
        self.restore_saved_export_settings()

    def export_canvas(self, target, format, canvas):
        """Export a single canvas."""
        for c in self.doc.canvases():
            if c.name() == canvas:
                self.og.windows.first().canvas.set(c)
                target = '%s.%s' % (os.path.join(target, canvas), format)
                self.export_item(target, format)
                return
        else:
            print "ERROR: canvas '%s' not found in document. List of existing canvases: \n%s" % (canvas, '\n'.join(self.get_canvas_list()))

    def export_item(self, fname, export_format):
        """Export an item."""

        export_path = fname

        def clear(path):
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.unlink(path)
                else:
                    shutil.rmtree(path)

        export_path_with_format = '%s.%s' % (export_path, export_format)
        if self.sandboxed():
            export_path = os.path.expanduser(
                self.SANDBOXED_DIR_6) + os.path.basename(fname)
            # TODO: when telling OmniGraffle to export to x, in some cases it exports to x.format
            # (is this with just one canvas in a document??)
            export_path_with_format = '%s.%s' % (export_path, export_format)
            clear(export_path)
            clear(export_path_with_format)

        self.doc.save(as_=export_format, in_=export_path)

        if self.sandboxed():
            clear(fname)
            if os.path.exists(export_path):
                os.rename(export_path, fname)
            else:
                os.rename(export_path_with_format, fname)

    def backup_current_export_settings(self):
        """Save current export settings so we can restore afterwards."""

        self.settings_backup[
            "area_type"] = self.og.current_export_settings.area_type()
        self.settings_backup[
            "border_amount"] = self.og.current_export_settings.border_amount()
        self.settings_backup[
            "resolution"] = self.og.current_export_settings.resolution()
        self.settings_backup[
            "export_scale"] = self.og.current_export_settings.export_scale()
        self.settings_backup[
            'draws_background'] = self.og.current_export_settings.draws_background()
        #self.settings_backup['html_image_type'] = self.og.current_export_settings.html_image_type()
        self.settings_backup[
            'include_border'] = self.og.current_export_settings.include_border()
        self.settings_backup[
            'origin'] = self.og.current_export_settings.origin()
        self.settings_backup['size'] = self.og.current_export_settings.size()

        if self.args.verbose:
            # display current export settings
            for k, v in self.settings_backup.items():
                print k, v

    def restore_saved_export_settings(self):

        self.og.current_export_settings.area_type.set(
            self.settings_backup['area_type'])
        self.og.current_export_settings.border_amount.set(
            self.settings_backup['border_amount'])
        self.og.current_export_settings.resolution.set(
            self.settings_backup['resolution'])
        self.og.current_export_settings.export_scale.set(
            self.settings_backup['export_scale'])
        self.og.current_export_settings.draws_background.set(
            self.settings_backup['draws_background'])
        # TODO: html image type can't be None - find out when this happens and how to avoid
        # self.og.current_export_settings.html_image_type.set(self.settings_backup['html_image_type'])
        self.og.current_export_settings.include_border.set(
            self.settings_backup['include_border'])
        self.og.current_export_settings.origin.set(
            self.settings_backup['origin'])
        self.og.current_export_settings.size.set(self.settings_backup['size'])

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

        if self.args.canvas:
            self.og.current_export_settings.area_type.set(
                appscript.k.current_canvas)
        else:
            self.og.current_export_settings.area_type.set(
                appscript.k.entire_document)

    def parse_commandline(self):
        """Parse commandline, do some checks and return args."""

        parser = argparse.ArgumentParser(description="Export canvases from OmniGraffle 6.",
                                         epilog=dedent("""
            If a file fails, simply try again. 

            Export uses current export settings stored in OmniGraffle for each filetype. 

            WARNING: Commandline arguments for scale or resolution override AND CHANGE export settings in OmniGraffle!"""))

        # TODO: add option for html image type: jpg, png, tiff
        # TODO: add option for overriding file name when exporting a single
        # canvase
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

        args = parser.parse_args()

        print 'exporting', args.source

        args.format = args.format.lower()
        # make sure target filename for multipage formats contains extension
        if args.format in self.MULTIPAGE_FORMATS:
            if not args.target.endswith('.' + args.format):
                args.target = '%s.%s' % (args.target, args.format)

        if args.format not in self.EXPORT_FORMATS:
            ArgumentParser.error("format '%s' not supported." % args.format)
            sys.exit(1)

        return args


def main():

    exporter = OmniGraffle6Exporter()
    exporter.export()


if __name__ == '__main__':
    main()
