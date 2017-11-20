#!/usr/bin/env python
from __future__ import print_function

import argparse
from collections import defaultdict
from functools import partial
import importlib
import logging
import pkgutil
import sys
import yaml


from omnigraffle.command import OmniGraffleSandboxedCommand

from omnigraffle.data_model import Document, TextContainer, Named, HasStroke, Filled
from colors import hexcolors, dump_colors_and_fonts_to_yaml_and_html
import ogplugins


"""
Translation of Omnigrafle files

1. Create Translation memory
    - get all cavases in file
    - for each canvas: get all text objects and dump to pot-file

2. Update translatiosn
    - create a copy of OmniGraffle source file language suffix
    - read po-file and make a translation dictionary d[msgid] = msgstr
        (replace newlines and quotes!!)
    - walk through all objects, if text: replace with translated text
    - save

TODO: how to make sure OmniGraffle files are not changed between exporting pot and tranlsation?
    Create dedicated image repo (needs branchens for each resource release) or add to the repo
     where illustrations are used (adds lots of duplication)

Do we need keys and template files?

    - create a key (hash) for each text
    - create a omnigraffle template file where texts are replaced by hashes
    - copy templates and fill in translations template files

"""

NONE = 'none'


class OmniGraffleSandboxedTools(OmniGraffleSandboxedCommand):
    """Some tools for OmniGraffle 6+"""

    def cmd_dump_colors_and_fonts(self):
        """
        Dump a list of all used colors and fonts.
        """

        self.open_document()
        colors = set()
        fonts = defaultdict(set)

        def extract(colors, fonts, element):
            logging.info(element.info)
            if isinstance(element, Named):
                logging.info('name %s' % element.name)
            if isinstance(element, HasStroke):
                logging.info('stroke color %s' % repr(element.stroke_color))
                colors.add(element.stroke_color)
            if isinstance(element, Filled):
                logging.info('fill color %s' % repr(element.fill_color))
                colors.add(element.fill_color)
            if isinstance(element, TextContainer):
                if element.text:  # element might still have no text
                    logging.info("-- text element: %s", " ".join((repr(element.text),
                                                                 repr(element.text_color),
                                                                 repr(element.text_font),
                                                                 repr(element.text_size),
                                                                 hexcolors(element.text_color))))
                    colors.add(element.text_color)
                    fonts[element.canvas_name].add(element.text_font)

        d = Document(self.doc)
        d.walk(partial(extract, colors, fonts))

        self.og.windows.first().close()
        dump_colors_and_fonts_to_yaml_and_html(self.args.source, colors, fonts)

    def cmd_replace(self):
        """Replace some fonts and colors in a copy of a document."""

        stream = open(self.args.replacements, "r")
        replacements = yaml.load(stream)

        logging.info(repr(replacements))
        # operate on a copy!!
        self.open_copy_of_document(self.args.document, suffix='replaced')

        def replace(replacements, element):
            if not isinstance(element, Document):
                logging.info(element.item.id(), element.item.class_(), element.__class__)
            if isinstance(element, Named):
                pass
            if isinstance(element, HasStroke):
                pass
            if isinstance(element, Filled):
                pass
            if isinstance(element, TextContainer):
                if element.item.text():  # element might still have no text
                    current_font = element.text.font()
                    try:
                        new_font = replacements['fonts'][current_font]
                    except KeyError:
                        new_font = NONE
                    logging.info(current_font, 'should be replaced by', new_font)
                    if new_font != NONE:
                        element.text.font.set(new_font)

        d = Document(self.doc)
        d.walk(partial(replace, replacements))
        self.og.windows.first().close()

    def cmd_run_plugin(self):
        """Run a plugin on a copy of a document."""

        if self.args.noconfig:
            config = {}
        else:
            stream = open(self.args.config, "r")
            config = yaml.load(stream)

        # operate on a copy!!
        self.open_copy_of_document(self.args.document, suffix=self.args.plugin)
        plugin = importlib.import_module("ogplugins.%s" % self.args.plugin, package='ogplugins')
        try:
            plugin = importlib.import_module("ogplugins.%s" % self.args.plugin, package='ogplugins')
        except ImportError, e:
            logging.critical("plugin %s not found" % self.args.plugin)
            raise e
            sys.exit(1)

        plugin.main(self.doc, config, self.args.canvas)

        self.og.windows.first().close()

    def cmd_list_plugins(self):
        """List all installed plugins."""

        print("Available plugins:\n")
        for importer, modname, ispkg in pkgutil.iter_modules(ogplugins.__path__):
            m = importer.find_module(modname).load_module(modname)
            # remove empty lines from docstring
            text = [s for s in m.__doc__.splitlines() if s.strip()]
            # doc = m.__doc__.splitlines()[0]
            print("%s: %s\n" % (modname, text[0]))

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                         description="Manipulate data in OmniGraffle documents.",
                                         epilog="If a file fails, simply try again.")

        subparsers = parser.add_subparsers()
        OmniGraffleSandboxedTools.add_parser_dump(subparsers)
        OmniGraffleSandboxedTools.add_parser_replace(subparsers)
        OmniGraffleSandboxedTools.add_parser_update(subparsers)
        OmniGraffleSandboxedTools.add_parser_list(subparsers)
        return parser

    @staticmethod
    def add_parser_dump(subparsers):
        sp = subparsers.add_parser('dump',
                                   help="Dump a list of all colors and fonts in an Omnigraffle document.")
        sp.add_argument('source', type=str,
                        help='an OmniGraffle file')
        sp.add_argument('--canvas', type=str,
                        help='select a canvas with given name')
        sp.set_defaults(func=OmniGraffleSandboxedTools.cmd_dump_colors_and_fonts)
        OmniGraffleSandboxedTools.add_verbose(sp)

    @staticmethod
    def add_parser_replace(subparsers):
        sp = subparsers.add_parser('replace',
                                   help="Replace some fonts and / or colors in an OmniGraffle document.")
        sp.add_argument('document', type=str,
                        help='an OmniGraffle file')
        sp.add_argument('replacements', type=str,
                        help='a yaml file with replacement for fonts and colors')
        sp.add_argument('--canvas', type=str,
                        help='select a canvas with given name')
        sp.set_defaults(func=OmniGraffleSandboxedTools.cmd_replace)
        OmniGraffleSandboxedTools.add_verbose(sp)

    @staticmethod
    def add_parser_update(subparsers):
        sp = subparsers.add_parser('run-plugin',
                                   help="Run a plugin on a copy of an OmniGraffle document .")
        sp.add_argument('plugin', type=str,
                        help='the plugin to use (must point to a file in plugins, file must implement a method main(document, config, canvas)')
        sp.add_argument('document', type=str,
                        help='an OmniGraffle file')
        sp.add_argument('--config', type=str,
                        help='a yaml file with configuration for the plugin')
        sp.add_argument('--noconfig', action='store_true',
                        help='skip loading config file')
        sp.add_argument('--canvas', type=str,
                        help='select a canvas with given name')
        sp.set_defaults(func=OmniGraffleSandboxedTools.cmd_run_plugin)
        OmniGraffleSandboxedTools.add_verbose(sp)

    @staticmethod
    def add_parser_list(subparsers):
        sp = subparsers.add_parser('list',
                                   help="List available plugins.")
        sp.set_defaults(func=OmniGraffleSandboxedTools.cmd_list_plugins)
        OmniGraffleSandboxedTools.add_verbose(sp)


def main():
    ogtool = OmniGraffleSandboxedTools()
    ogtool.args.func(ogtool)


if __name__ == '__main__':
    main()
