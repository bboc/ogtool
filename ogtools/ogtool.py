#!/usr/bin/env python

import argparse
import codecs
from collections import defaultdict
from functools import partial
import importlib
import os
import pkgutil

import shutil
from string import Template
import sys
from textwrap import dedent

import appscript
import polib
import yaml


from omnigraffle.command import OmniGraffleSandboxedCommand

from omnigraffle.data_model import Document, Canvas, TextContainer, Named, HasStroke, Filled
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
        def extract(colors, fonts, verbosity, element):
            if verbosity > 3 and not isinstance(element, Document):
                print element.item.id(), element.item.class_(), element.__class__
            if isinstance(element, Named):
                if verbosity > 2:
                    print 'name', element.name
            if isinstance(element, HasStroke):
                if verbosity > 2:
                    print 'stroke color', element.stroke_color
                colors.add(element.stroke_color)
            if isinstance(element, Filled):
                if verbosity > 2:
                    print 'fill color', element.fill_color
                colors.add(element.fill_color)
            if isinstance(element, TextContainer):
                if element.item.text(): # element might still have no text
                    if verbosity > 1:
                        print "-- text element:", repr(element.item.text()), repr(element.text.color()), repr(element.text.font()), repr(element.text.size()), hexcolors(element.text.color())
                    colors.add(element.text.color())
                    fonts[element.canvas_name].add(element.text.font())

        d = Document(self.doc)
        d.walk(partial(extract, colors, fonts, self.args.verbose))

        self.og.windows.first().close()
        dump_colors_and_fonts_to_yaml_and_html(self.args.source, colors, fonts)
    
    def cmd_replace(self):
        """Replace some fonts and colors in a copy of a document."""

        stream = open(self.args.replacements, "r")
        replacements = yaml.load(stream)

        print repr(replacements)
        # operate on a copy!!
        self.open_copy_of_document(self.args.document, 'replaced')

        def replace(replacements, verbosity, element):
            if verbosity > 2 and not isinstance(element, Document):
                print element.item.id(), element.item.class_(), element.__class__
            if isinstance(element, Named):
                pass
            if isinstance(element, HasStroke):
                pass
            if isinstance(element, Filled):
                pass
            if isinstance(element, TextContainer):
                if element.item.text(): # element might still have no text
                    current_font = element.text.font()
                    try:
                        new_font = replacements['fonts'][current_font]
                    except KeyError:
                        new_font = NONE
                    print current_font, 'should be replaced by', new_font
                    if new_font != NONE:
                        element.text.font.set(new_font)

        d = Document(self.doc)
        d.walk(partial(replace, replacements, self.args.verbose))
        self.og.windows.first().close()


    def cmd_run_plugin(self):
        """Run a plugin on a copy of a document."""

        stream = open(self.args.config, "r")
        config = yaml.load(stream)

        # operate on a copy!!
        self.open_copy_of_document(self.args.document, self.args.plugin)
        plugin = importlib.import_module("ogplugins.%s" % self.args.plugin, package='ogplugins')
        try: 
            plugin = importlib.import_module("ogplugins.%s" % self.args.plugin, package='ogplugins')
        except ImportError, e:
            print "plugin %s not found" % self.args.plugin
            raise e
            sys.exit(1)

        plugin.main(self.doc, config, self.args.canvas, self.args.verbose)

        self.og.windows.first().close()


    def cmd_list_plugins(self):
        """List all installed plugins."""

        print "Available plugins:\n"
        for importer, modname, ispkg in pkgutil.iter_modules(ogplugins.__path__):
            m = importer.find_module(modname).load_module(modname)
            # remove empty lines from docstring
            text = [s for s in m.__doc__.splitlines() if s.strip()]
            # doc = m.__doc__.splitlines()[0]
            print "%s: %s\n" % (modname, text[0])

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
        sp.add_argument('--verbose', '-v', action='count')
        sp.set_defaults(func=OmniGraffleSandboxedTools.cmd_dump_colors_and_fonts)


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
        sp.add_argument('--verbose', '-v', action='count')
        sp.set_defaults(func=OmniGraffleSandboxedTools.cmd_replace)

    @staticmethod
    def add_parser_update(subparsers):
        sp = subparsers.add_parser('run-plugin',
                                   help="Run a plugin on a copy of an OmniGraffle document .")
        sp.add_argument('plugin', type=str,
                            help='the plugin to use (must point to a file in plugins, file must implement a method main(document, config, canvas, verbose)')
        sp.add_argument('document', type=str,
                            help='an OmniGraffle file')
        sp.add_argument('config', type=str,
                            help='a yaml file with configuration for the plugin')
        sp.add_argument('--canvas', type=str,
                            help='select a canvas with given name')
        sp.add_argument('--verbose', '-v', action='count')
        sp.set_defaults(func=OmniGraffleSandboxedTools.cmd_run_plugin)

    @staticmethod
    def add_parser_list(subparsers):
        sp = subparsers.add_parser('list',
                                   help="List available plugins.")
        sp.set_defaults(func=OmniGraffleSandboxedTools.cmd_list_plugins)

def main():
    ogtool = OmniGraffleSandboxedTools()
    ogtool.args.func(ogtool)


if __name__ == '__main__':
    main()
