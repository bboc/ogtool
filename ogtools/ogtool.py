#!/usr/bin/env python

import argparse
import codecs
from collections import defaultdict
from functools import partial
import importlib
import os
import shutil
from string import Template
import sys
from textwrap import dedent

import appscript
import polib
import yaml


from omnigraffle.command import OmniGraffleSandboxedCommand

from omnigraffle.data_model import Document, Canvas, TextContainer, Named, HasStroke, Filled

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
        fonts = set()
        def extract(colors, fonts, verbosity, element):
            if verbosity > 2 and not isinstance(element, Document):
                print element.item.id(), element.item.class_(), element.__class__
            if isinstance(element, Named):
                if verbosity > 2:
                    print 'name', element.name
            if isinstance(element, HasStroke):
                if verbosity > 1:
                    print 'stroke color', element.stroke_color
                colors.add(element.stroke_color)
            if isinstance(element, Filled):
                if verbosity > 1:
                    print 'fill color', element.fill_color
                colors.add(element.fill_color)
            if isinstance(element, TextContainer):
                if element.item.text(): # element might still have no text
                    if verbosity:
                        print "-- text element:", repr(element.item.text()), repr(element.text.color()), repr(element.text.font()), repr(element.text.size()), OmniGraffleSandboxedTools.hexcolors(element.text.color())
                    colors.add(element.text.color())
                    fonts.add(element.text.font())

        d = Document(self.doc)
        d.walk(partial(extract, colors, fonts, self.args.verbose))

        self.og.windows.first().close()
        self.html_color_palette(colors, fonts)
    
    @staticmethod
    def hexcolors(color):
        try: 
            return ''.join(['{0:#04x}'.format(c/256)[2:] for c in color]).upper()
        except TypeError:
            return '--unknown--'

    def html_color_palette(self, colors, fonts):
        RED = 0
        GREEN = 1
        BLUE = 2
        GRAY = 3

        color_groups = [(GRAY, 'grays'), (RED, 'reds'), (GREEN, 'greens'), (BLUE, 'blues')]

        grouped_colors = defaultdict(list) # the colors grouped by most prominent component
        HTML = Template(dedent("""
            <html>
            <head><title>Color Palette</title></head>
            <body>
            <div style="float: left; width: 48%;">
            <h1>Color Groups</h1>

            $color_groups
            </div><div style="float: right; width: 48%;">
            <h1>YAML-File</h1>
            <pre>
            <strong>fonts:</strong>
            $yaml_fonts
            <strong>colors:</strong>
            $yaml_colors
            </pre>
            </div>
            </body></html>"""))
        YAML = Template(dedent("""
            fonts:
            $yaml_fonts
            colors:
            $yaml_colors
        """))
        COLORBOX = """<p><span style="background-color: #%(color)s">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span> #%(color)s </p>\n"""
        YAML_COLOR = """    x%(color)s: none"""
        YAML_COLOR_HTML = """<span style="background-color: #%(color)s">&nbsp;&nbsp;&nbsp;&nbsp;- </span> c%(color)s: none"""
        
        YAML_FONT = """    %s: none"""
        YAML_FONT_HTML = """&nbsp;&nbsp;&nbsp;&nbsp;- %s: none"""
        COLOR_HEADER = "<h2>%s</h2>\n"
        
        def primary_color(color):
            """determine whether a color is either a red, a green, a blue or a gray."""
            def check(c, reference, other1, other2):
                if c[reference] > c[other1] and c[reference] >= c[other2]:
                    return True
                return False
            if check(c, RED, GREEN, BLUE):
                return RED
            elif check(c, GREEN, RED, BLUE):
                return GREEN
            elif check(c, BLUE, RED, GREEN):
                return BLUE
            else:
                return GRAY

        # sort colors into groups
        for c in colors: 
            grouped_colors[primary_color(c)].append(c)
            #print c, OmniGraffleSandboxedTools.hexcolors(c), primary_color(c)
        
        color_groups_html = []
        yaml_colors = []
        yaml_colors_html = []
        for cindex, cname in color_groups:
            color_groups_html.append(COLOR_HEADER % cname)
            for color in sorted(grouped_colors[cindex], key=OmniGraffleSandboxedTools.hexcolors):
                color_groups_html.append(COLORBOX % dict(color=OmniGraffleSandboxedTools.hexcolors(color)))
                yaml_colors.append(YAML_COLOR % dict(color=OmniGraffleSandboxedTools.hexcolors(color)))
                yaml_colors_html.append(YAML_COLOR_HTML % dict(color=OmniGraffleSandboxedTools.hexcolors(color)))

        yaml_fonts = []
        yaml_fonts_html = []
        for f in sorted(fonts):
            yaml_fonts.append(YAML_FONT % f)
            yaml_fonts_html.append(YAML_FONT_HTML % f)


        target_path = os.path.splitext(os.path.split(self.args.source)[1])[0]
        with codecs.open(target_path + ".html", 'w+', 'utf-8') as fp:
            fp.write(HTML.substitute(color_groups='\n'.join(color_groups_html), 
                                    yaml_fonts='\n'.join(yaml_fonts_html),
                                    yaml_colors='\n'.join(yaml_colors_html)))
        with codecs.open(target_path + ".yaml", 'w+', 'utf-8') as fp:
            fp.write(YAML.substitute(yaml_fonts='\n'.join(yaml_fonts),
                                     yaml_colors='\n'.join(yaml_colors)))


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

        plugin.main(self.doc, config, self.args.canvas, self.args.verbose)

        self.og.windows.first().close()


    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                         description="Manipulate some stuff in omnigraffle documents.",
                                         epilog="If a file fails, simply try again.")

        subparsers = parser.add_subparsers()
        OmniGraffleSandboxedTools.add_parser_dump(subparsers)
        OmniGraffleSandboxedTools.add_parser_replace(subparsers)
        OmniGraffleSandboxedTools.add_parser_update(subparsers)
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


def main():
    ogtool = OmniGraffleSandboxedTools()
    ogtool.args.func(ogtool)


if __name__ == '__main__':
    main()
