#!/usr/bin/env python

import argparse
import logging
import os
import shutil
import sys
import tempfile

from textwrap import dedent
import appscript

EXPORT_FORMATS = [
    'bmp', 
    'eps', 
    'gif', 
    # 'html' NOT WORKING (OSERROR -50 "The document cannot be exported to the "HTML text" format."
    'jpg', 
    'png', 
    'pdf', 
    'psd', # Photoshop
    # 'svg' NOT WORKING (OSERROR -50 "The document cannot be exported to the "scalable vector graphics (SVG)" format.")
    'tiff',
    'vdx', # Visio XML
]
MULTIPAGE_FORMATS = ('pdf', 'vdx')

SANDBOXED_DIR_6 = '~/Library/Containers/com.omnigroup.OmniGraffle6/Data/'


def export(args):

    og = appscript.app('OmniGraffle')
    og.activate()


    doc = og.open(os.path.abspath(args.source))

    if not doc:
        # fix for inaccessible files
        import subprocess
        subprocess.call(['open',os.path.abspath(args.source)])
        doc = og.open(os.path.abspath(args.source))

    target = os.path.abspath(args.target)

    if args.transparent:
        og.current_export_settings.draws_background.set(False)
    else:
        og.current_export_settings.draws_background.set(True)
    if args.resolution:
        og.current_export_settings.resolution.set(args.resolution)
    if args.scale:
        og.current_export_settings.export_scale.set(args.scale)

    if args.canvas:
        # TODO test and fix
        og.current_export_settings.area_type.set(appscript.k.current_canvas)
        export_canvas(og, args)
    else:
        og.current_export_settings.area_type.set(appscript.k.entire_document)

        export_item(og, doc, target, args.format)

    og.windows.first().close()

def export_canvas(og, doc, target, args):
    # TODO: this is totally untested
    for canvas in doc.canvases():
        og.windows.first().canvas.set(canvas)
        og.current_export_settings.area_type.set(appscript.k.current_canvas)
        
        og.windows.first().canvas.set(canvas)
        format = 'eps'
        export_format = EXPORT_FORMATS[format]

        fname = '/Users/beb/dev/omnigraffle-export/omnigraffle_export/tmp/%s.%s' % (canvas.name(), format)

        export_item(og, fname, export_format)


def export_item(og, doc, fname, export_format):
    """Export an item."""
 
    # Is OmniGraffle sandboxed?
    # real check using '/usr/bin/codesign --display --entitlements - /Applications/OmniGraffle.app'
    sandboxed = og.version()[0] == '6' and os.path.exists(os.path.expanduser(SANDBOXED_DIR_6))

    export_path = fname

    export_path_with_format = '%s.%s' % (export_path, export_format.lower())
    if sandboxed:
        export_path = os.path.expanduser(SANDBOXED_DIR_6) + os.path.basename(fname)

        # when telling OmniGraffle to export to x, in some cases it exports to x.format -- weird
        export_path_with_format = '%s.%s' % (export_path, export_format.lower())
        # TODO: unlink in case of file when exporting  individual canvas
        if os.path.exists(export_path):
            shutil.rmtree(export_path)
        if os.path.exists(export_path_with_format):
            shutil.rmtree(export_path_with_format)
        logging.debug('OmniGraffle is sandboxed - exporting to: %s' % export_path)


    doc.save(as_=export_format, in_=export_path)
    
    if sandboxed:
        if os.path.exists(fname):
            shutil.rmtree(fname)        
        if os.path.exists(export_path):
            os.rename(export_path, fname)
        else:
            os.rename(export_path_with_format, fname)    
        logging.debug('OmniGraffle is sandboxed - moving %s to: %s' % (export_path, fname))


def main():

    parser = argparse.ArgumentParser(description="Export canvases from OmniGraffle 6.",
                                     epilog= dedent("""
        If a file fails, simply try again. 

        Export uses current export settings stored in OmniGraffle for each filetype. 

        WARNING: Commandline arguments for scale or resolution override AND CHANGE export settings in OmniGraffle!"""))

    # TODO: add html image type: jpg, png, tiff
    parser.add_argument('format', type=str,
                    help="Export formats: bmp, eps, gif, jpg, png, pdf, psd (Photoshop), tiff, vdx (Visio XML) (not supported: html, svg)")
    
    parser.add_argument('source', type=str,
                    help='an OmniGraffle file')
    parser.add_argument('target', type=str,
                    help='folder to export to')
    # TODO: implement 
    parser.add_argument('--canvas', type=str,
                        help='export canvas with given name')
    parser.add_argument('--scale', type=float,
                        help=' The scale to use during export (1.0 is 100%%)')
    parser.add_argument('--resolution', type=float,
                        help='The number of pixels per point in the resulting exported image (1.0 for 72 DPI)')
    parser.add_argument('--transparent', dest='transparent', action='store_true',
                        help='export with transparent background')

    args = parser.parse_args()

    print 'exporting', args.source
    print args

    # make sure target filename for multipage formats contains extension
    if args.format.lower() in MULTIPAGE_FORMATS:
        if not args.target.endswith('.'+args.format.lower()):
            args.target = '%s.%s' % (args.target, args.format.lower())

    if args.format.lower() not in EXPORT_FORMATS:
        print "ERROR: format '%s' not supported." % args.format
        sys.exit(1)

    export(args)    


if __name__ == '__main__':
    main()

