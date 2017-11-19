#!/usr/bin/env python

import argparse
from collections import defaultdict
from functools import partial
import os

import polib

from omnigraffle.command import OmniGraffleSandboxedCommand
from omnigraffle.data_model import Canvas, TextContainer

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

BLACK = (0, 0, 0)
ALMOST_BLACK = (1, 1, 1)


class OmniGraffleSandboxedTranslator(OmniGraffleSandboxedCommand):
    """Translator for OmniGraffle6"""

    def cmd_extract_translations(self):
        """
        Extract translations from an OmniGraffle document to a POT file.

        Translation memory is compiled in defaultdict (of sets) that has the messages as keys
        so duplicates are automatically eliminated, and locations are collected as a set, again
        to eliminate duplicates.
        """
        self.open_document()

        def extract_translations(file_name, canvas_name, translation_memory, element):
            if isinstance(element, TextContainer):
                # add text to memory
                location = "%s/%s" % (file_name, canvas_name)
                translation_memory[element.text].add(location)

        file_name = os.path.basename(self.args.source)
        translation_memory = defaultdict(set)
        for canvas in self.doc.canvases():
            c = Canvas(canvas)
            c.walk(partial(extract_translations, file_name, canvas.name(), translation_memory))

        self.og.windows.first().close()
        self.dump_translation_memory(translation_memory)

    def dump_translation_memory(self, tm):
        """
        Dump translation memory to a pot-file.

        Sort messages in pot-file by location (if there's more locations, sort locations
        alphabetiaclly first) so that translators can process canvases alphabetially and
        easily review exported images in a folder one by one.
        """
        container = []
        for text, locations in tm.items():
            container.append((sorted([l for l in locations]), text))
        container.sort(key=lambda x: x[0][0])

        pot = polib.POFile()
        for locations, text in container:
            entry = polib.POEntry(
                msgid=text,
                msgstr=text,
                occurrences=[(location, '0') for location in locations]
            )
            pot.append(entry)
        pot.save(os.path.splitext(self.args.source)[0] + '.pot')

    def cmd_list(self):
        """List all canvases in file."""

        self.open_document(self.args.source)
        for canvas in self.doc.canvases():
            print "%s (in %s) " % (canvas.name(),
                                   os.path.splitext(self.args.source)[0])
        self.og.windows.first().close()

    def cmd_translate(self):
        """Inject translations from a po-file into an OmniGraffle document."""

        tm = self.read_translation_memory(self.args.po_file)
        self.open_copy_of_document(self.args.document, self.args.language)

        def inject_translations_legacy(tm, element):
            """
            Translate attribute_runs of an element. This code loses all formatting,
            but successfully set marks an element as modified.
            """
            if element.text:  # element has more than zero length accessible text
                if element.text in tm:
                    element.item.text.set(tm[element.text])

        def inject_translations(tm, element):
            """Translate attribute_runs of an element."""
            if element.text:  # element has more than zero length accessible text
                for idx in range(len(element.item.text.attribute_runs())):
                    text = element.item.text.attribute_runs[idx].text()
                    if text in tm:
                        element.item.text.attribute_runs[idx].text.set(tm[text])
                        toggle_dirty_bit_for_element(element)

        def toggle_dirty_bit_for_element(element):
            """
            OmniGraffle 6 does not detect that a text run has changed, so we attempt
            to notify it through another change (text color) to the parent element,
            which is then instantly reverted.
            """
            original_color = element.item.text.color()
            # make sure any color is toggled
            if original_color == BLACK:
                element.item.text.color.set(ALMOST_BLACK)
            else:
                element.item.text.color.set(BLACK)
            # print element.item.class_(), element.text, self.doc.modified()
            # revert the change again
            element.item.text.color.set(original_color)

        for canvas in self.doc.canvases():
            c = Canvas(canvas)
            c.walk(partial(inject_translations, tm))
        self.og.windows.first().close()

    def read_translation_memory(self, filename):
        """Read translation memory from a po-file."""
        tm = {}
        po = polib.pofile(filename)
        for entry in po.translated_entries():
            if not entry.obsolete:
                tm[entry.msgid] = entry.msgstr
        return tm

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                         description="Translate canvases in OmniGraffle 6.",
                                         epilog="If a file fails, simply try again.")

        subparsers = parser.add_subparsers()
        OmniGraffleSandboxedTranslator.add_parser_extract(subparsers)
        OmniGraffleSandboxedTranslator.add_parser_list(subparsers)
        OmniGraffleSandboxedTranslator.add_parser_translate(subparsers)
        return parser

    @staticmethod
    def add_parser_extract(subparsers):
        sp = subparsers.add_parser('extract',
                                   help="Extract a POT file from an Omnigraffle document.")
        sp.add_argument('source', type=str,
                        help='an OmniGraffle file')
        sp.add_argument('--canvas', type=str,
                        help='translate canvas with given name')
        OmniGraffleSandboxedTranslator.add_verbose(sp)
        sp.set_defaults(func=OmniGraffleSandboxedTranslator.cmd_extract_translations)

    @staticmethod
    def add_parser_list(subparsers):
        sp = subparsers.add_parser('list',
                                   help="List canvases in a file.")
        sp.add_argument('source', type=str,
                        help='an OmniGraffle file')
        OmniGraffleSandboxedTranslator.add_verbose(sp)
        sp.set_defaults(func=OmniGraffleSandboxedTranslator.cmd_list)

    @staticmethod
    def add_parser_translate(subparsers):
        sp = subparsers.add_parser('translate',
                                   help="Translate an Omnigraffle document with strings from a po file.")
        sp.add_argument('document', type=str,
                        help='an OmniGraffle file')
        sp.add_argument('language', type=str,
                        help='two-digit language identifier')
        sp.add_argument('po_file', type=str,
                        help='name of po-file')
        sp.add_argument('--canvas', type=str,
                        help='translate canvas with given name')
        OmniGraffleSandboxedTranslator.add_verbose(sp)
        sp.set_defaults(func=OmniGraffleSandboxedTranslator.cmd_translate)


def main():
    translator = OmniGraffleSandboxedTranslator()
    translator.args.func(translator)


if __name__ == '__main__':
    main()
