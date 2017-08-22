# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import unittest

from PIL import Image

from omnigraffle_export.omnigraffle6_export import OmniGraffle6Exporter

"""
nosetests test_omnigraffle6_export.py:SimpleFormatTests
#print os.listdir(self.results_dir)

"""


class OG6TestCase(unittest.TestCase):

    def setUp(self):
        """Create temp folder, copy test case data."""
        self.document = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_data', 'basic', 'test.graffle')

        self.results_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.results_dir)
        self.parser = OmniGraffle6Exporter.get_parser()
        self.target = None

    def _basic_export(self, format, *more_args):
        if not self.target:
            self.target = os.path.join(self.results_dir, 'my-export')
        command = [format, self.document, self.target]
        command.extend(more_args)
        print command
        args = self.parser.parse_args(command)

        print os.listdir(self.results_dir)
        print self.results_dir
        print self.target
        # make sure export don't exist
        self.assertFalse(os.path.exists(self.target))

        exporter = OmniGraffle6Exporter(args)
        exporter.export()

    def image_stats(self, fname):
        im = Image.open(fname)
        res = (im.format, im.width, im.height)
        im.close()
        return res


class MultiPageFormatTests(OG6TestCase):

    def test_pdf_export(self):
        self._basic_export('pdf')
        self.assertTrue(os.path.exists(os.path.join(self.target, 'test.pdf')))

    def test_visio_export(self):
        self._basic_export('vdx')
        self.assertTrue(os.path.exists(os.path.join(self.target, 'test.vdx')))


class SimpleFormatTests(OG6TestCase):

    """Make sure all formats are exported correctly."""

    def _export_format(self, format, format_name):

        self._basic_export(format)
        self.assertTrue(os.path.exists(self.target))

        res_fname = os.path.join(self.target, 'Canvas 1.%s' % format)
        self.assertTrue(os.path.exists(res_fname))
        res_format = self.image_stats(res_fname)[0]
        self.assertEqual(res_format, format_name)

    def test_bmp(self):
        self._export_format('bmp', "BMP")

    def test_eps(self):
        self._export_format('eps', 'EPS')

    def test_gif(self):
        self._export_format('gif', 'GIF')

    def test_jpg(self):
        self._export_format('jpg', 'JPEG')

    def test_png(self):
        self._export_format('png', 'PNG')

    # TODO: this test hangs
    # def test_psd(self):
    #     self._export_format('psd', 'PSD')

    def test_tiff(self):
        self._export_format('tiff', 'TIFF')


class BasicTests(OG6TestCase):

    def test_file_with_one_canvas(self):

        self.document = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_data', 'basic', 'one-canvas.graffle')

        self._basic_export('png')
        self.assertTrue(os.path.exists(self.target))

        # check canvas file and format
        canvas_fname = os.path.join(self.target, 'the-canvas.png')
        self.assertTrue(os.path.exists(canvas_fname))
        c_format = self.image_stats(canvas_fname)[0]
        self.assertEqual(c_format, 'PNG')

    def test_file_with_two_canvases(self):

        self._basic_export('png')
        self.assertTrue(os.path.exists(self.target))

        # check canvas 1 file and format
        canvas1_fname = os.path.join(self.target, 'Canvas 1.png')
        print canvas1_fname
        self.assertTrue(os.path.exists(canvas1_fname))
        c1_format = self.image_stats(canvas1_fname)[0]
        self.assertEqual(c1_format, 'PNG')

        # check canvas 2 file and format
        canvas2_fname = os.path.join(self.target, 'Canvas 2.png')
        self.assertTrue(os.path.exists(canvas2_fname))
        c2_format = self.image_stats(canvas2_fname)[0]
        self.assertEqual(c2_format, 'PNG')


class SingleCanvasExportTests(OG6TestCase):

    def test_existing_canvas(self):
        self.document = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_data', 'basic', 'one-canvas.graffle')

        self._basic_export('png', "--canvas=the-canvas")

        self.assertTrue(os.path.exists(self.target))

        # check canvas file and format
        canvas_fname = os.path.join(self.target, 'the-canvas.png')
        self.assertTrue(os.path.exists(canvas_fname))
        c_format = self.image_stats(canvas_fname)[0]
        self.assertEqual(c_format, 'PNG')

    def test_missing_canvas(self):
        self.document = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_data', 'basic', 'one-canvas.graffle')

        self.assertRaises(
            SystemExit, self._basic_export, 'png', "--canvas=not-a-canvas")


class OptionalArgumentTests(OG6TestCase):

    """Test PNG format in more detail to make sure options are processed correctly."""

    def test_scale(self):
        pass  # TODO

    def test_resolution(self):
        pass  # TODO

    def test_transparency(self):
        pass  # TODO
