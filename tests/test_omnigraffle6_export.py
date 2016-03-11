# -*- coding: utf-8 -*-

import os
import shutil
import sys
import tempfile
import unittest

from PIL import Image

from omnigraffle_export.omnigraffle6_export import OmniGraffle6Exporter

# TODO: make sure multipart document names can contain extension


class OG6TestCase(unittest.TestCase):

    def setUp(self):
        """Create temp folder, copy test case data."""
        self.document = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_data', 'basic', 'test.graffle')
        self.one_canvas = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test_data', 'basic', 'one_canvas.graffle')

        self.results_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.results_dir)
        self.parser = OmniGraffle6Exporter.get_parser()

    def image_stats(self, fname):
        im = Image.open(fname)
        res = (im.format, im.width, im.height)
        im.close()
        return res


class MultiPageFormatTests(OG6TestCase):

    def test_pdf_export(self):

        target = os.path.join(self.results_dir, 'mypdf')
        args = self.parser.parse_args(['pdf', self.document, target])

        # make sure backups don't exist
        self.assertFalse(os.path.exists(target))

        exporter = OmniGraffle6Exporter(args)
        exporter.export()

        self.assertTrue(os.path.exists(target+'.pdf'), target)

    def test_visio_export(self):

        target = os.path.join(self.results_dir, 'myvisio')
        args = self.parser.parse_args(['pdf', self.document, target])

        # make sure backups don't exist
        self.assertFalse(os.path.exists(target))

        exporter = OmniGraffle6Exporter(args)
        exporter.export()

        self.assertTrue(os.path.exists(target+'.vdx'), target)


class SimpleFormatTests(OG6TestCase):
    """Make sure all formats are exported correctly."""
    FORMATS_TO_TEST = [
        'bmp',
        'eps',
        'gif',
        # 'html' TODO: NOT WORKING (OSERROR -50 "The document cannot be exported to the "HTML text" format."
        'jpg',
        'png',
        'psd',  # Photoshop
        # 'svg' TODO: NOT WORKING (OSERROR -50 "The document cannot be exported to the "scalable vector graphics (SVG)" format.")
        'tiff',
    ]

    def test_simple_formats(self):
        pass # TODO


class SingleCanvasExportTests(OG6TestCase):

    def test_existing_canvas(self):
        pass # TODO

    def pass_missing_canvas(self):
        pass # TODO

class OptionalArgumentTests(OG6TestCase):
    """Test PNG format in more detail to make sure options are processed correctly."""

    def test_scale(self):
        pass # TODO

    def test_resolution(self):
        pass # TODO

    def test_transparency(self):
        pass # TODO



