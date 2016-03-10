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
    # 'html' TODO: NOT WORKING (OSERROR -50 "The document cannot be exported to the "HTML text" format."
    'jpg', 
    'png', 
    'pdf', 
    'psd', # Photoshop
    # 'svg' TODO: NOT WORKING (OSERROR -50 "The document cannot be exported to the "scalable vector graphics (SVG)" format.")
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


    #og.current_export_settings.border_amount.set(0)
    #og.current_export_settings.include_border.set(False)

    # display current export settings
    if args.verbose:
        print "current export settings:"
        print "resolution", og.current_export_settings.resolution()
        print "scale", og.current_export_settings.export_scale()
        print "border amount", og.current_export_settings.border_amount()
        print 'include border', og.current_export_settings.include_border()
        print 'html image type', og.current_export_settings.html_image_type()
        print 'draws background', og.current_export_settings.draws_background()
        print 'origin', og.current_export_settings.origin()
        print 'size', og.current_export_settings.size()


    if args.canvas:
        og.current_export_settings.area_type.set(appscript.k.current_canvas)
        if args.verbose: print 'area type', og.current_export_settings.area_type()

        export_canvas(og, doc, target, args.format, args.canvas)
    else:
        og.current_export_settings.area_type.set(appscript.k.entire_document)
        if args.verbose: print 'area type', og.current_export_settings.area_type()

        export_item(og, doc, target, args.format)

    og.windows.first().close()

def export_canvas(og, doc, target, format, canvas):
    canvas_names = []
    for c in doc.canvases():
        canvas_names.append(c.name())
        if c.name() == canvas:
            og.windows.first().canvas.set(c)
            og.current_export_settings.area_type.set(appscript.k.current_canvas)
            target = '%s.%s' % (os.path.join(target, canvas), format)
            export_item(og, doc, target, format)
            return
    else:
        print "ERROR: canvas '%s' not found in document. List of existing canvases: \n%s" % (canvas, '\n'.join(canvas_names))

def export_item(og, doc, fname, export_format):
    """Export an item."""
 
    # Is OmniGraffle sandboxed?
    # real check using '/usr/bin/codesign --display --entitlements - /Applications/OmniGraffle.app'
    sandboxed = og.version()[0] == '6' and os.path.exists(os.path.expanduser(SANDBOXED_DIR_6))

    export_path = fname

    def clear(path):
        if os.path.exists(path):
            if os.path.isfile(path):
                os.unlink(path)
            else:
                shutil.rmtree(path)

    export_path_with_format = '%s.%s' % (export_path, export_format)
    if sandboxed:
        export_path = os.path.expanduser(SANDBOXED_DIR_6) + os.path.basename(fname)

        # when telling OmniGraffle to export to x, in some cases it exports to x.format -- weird
        export_path_with_format = '%s.%s' % (export_path, export_format)
        clear(export_path)
        clear(export_path_with_format)

        logging.debug('OmniGraffle is sandboxed - exporting to: %s' % export_path)


    doc.save(as_=export_format, in_=export_path)
    
    if sandboxed:
        clear(fname)
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

    # TODO: add option for html image type: jpg, png, tiff
    # TODO: add option for overriding file name when exporting a single canvase
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
    if args.format in MULTIPAGE_FORMATS:
        if not args.target.endswith('.'+args.format):
            args.target = '%s.%s' % (args.target, args.format)

    if args.format not in EXPORT_FORMATS:
        ArgumentParser.error("format '%s' not supported." % args.format)
        sys.exit(1)

    export(args)    


if __name__ == '__main__':
    main()

