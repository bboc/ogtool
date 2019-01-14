#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from collections import defaultdict
from datetime import datetime
from functools import partial
import logging
import os
from textwrap import dedent
import polib

import appscript
from omnigraffle.command import OmniGraffleSandboxedCommand
from omnigraffle.data_model import Canvas

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

TODO: how to make sure OmniGraffle files are not changed between exporting pot and translation?
    Create dedicated image repo (needs branchens for each resource release) or add to the repo
     where illustrations are used (adds lots of duplication)

Do we need keys and template files?

    - create a key (hash) for each text
    - create a omnigraffle template file where texts are replaced by hashes
    - copy templates and fill in translations template files
"""

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

        def extract_translations_legacy(file_name, canvas_name, translation_memory, element):
            if element.text:
                # add text to memory
                location = "%s/%s" % (file_name, canvas_name)
                translation_memory[element.text].add(location)

        def extract_translations(file_name, canvas_name, translation_memory, element):
            if element.text:  # element has more than zero length accessible text
                for text in element.item.text.attribute_runs():
                    if text.strip():  # add only text with non-whitespace memory
                        location = "%s/%s" % (file_name, canvas_name)
                        translation_memory[text].add(location)

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
        """
        Inject translations from a po-files into  OmniGraffle documents.

        If any of the parameters is a directory, actual filenames will be
        inferred from source file, if source is a directory, all OmniGraffle
        documents in that folder will be processed.
        """

        if not os.path.exists(self.args.source):
            logging.error("source '%s' does not exist", self.args.source)
            return

        if os.path.isdir(self.args.source):
            for filename in sorted(os.listdir(self.args.source)):
                if filename.endswith(".graffle"):
                    self.translate_document(os.path.join(self.args.source, filename),
                                            self.args.target,
                                            self.args.translations)
        else:
            self.translate_document(self.args.source, self.args.target, self.args.translations)

    def translate_document(self, source, target, translations):
        """Create a copy of and then translate one OmniGraffle document."""
        self.open_copy_of_document(source, target=target)
        if os.path.isdir(translations):
            tm_file = os.path.join(translations, os.path.splitext(os.path.basename(source))[0] + '.po')
        else:
            tm_file = translations
        tm = self.read_translation_memory(tm_file)

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
            # import pdb; pdb.set_trace()

            if element.text:  # element has more than zero length accessible text
                for idx in range(len(element.item.text.attribute_runs())):
                    text = element.item.text.attribute_runs[idx].text()
                    logging.debug("found text: '%s'", text)
                    if text in tm:
                        # import pdb; pdb.set_trace()
                        element.item.text.attribute_runs[idx].text.set(tm[text])
                        toggle_dirty_bit_for_element(element)
                        # try:
                        #     logging.info("translate text: '%s' -> '%s' (modified: %s)", text, tm[text], self.doc.modified())
                        #     element.item.text.attribute_runs[idx].text.set(tm[text])
                        #     toggle_dirty_bit_for_element(element)
                        # except appscript.reference.CommandError:
                        #     logging.error("unable to replace '%s' with '%s' in %s", text, tm[text], element.info)

        def toggle_dirty_bit_for_element(element):
            """
            As changing an text in an attribute run does not trigger a document save, the element containg
            the text gets an updated timestamp in it's user data container. Now changes are saved correctly.
            """
            data = element.item.user_data()
            data = data or {}
            data['upd_timestamp'] = str(datetime.now())
            element.item.user_data.set(data)
            if not self.doc.modified():
                logging.error("document is not marked as modified")

        for canvas in self.doc.canvases():
            c = Canvas(canvas)
            c.walk(partial(inject_translations, tm))

        self.og.windows.first().save()
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
                                   description=dedent("""Translate an Omnigraffle document(s) using po-files.

                                        If any of the parameters is a directory, actual filenames will be
                                        inferred from source file, if source is a directory, all OmniGraffle
                                        documents in that folder will be processed.
                                        Example:

                                           ogtranslate translate graffle/src/ graffle/de/ text/de/

                                        will create translated copies from each document found in graffle/src
                                        in graffle/de, using a separate po-file for each document, located
                                        in graffle/de.

                                            ogtranslate translate graffle/src/ graffle/de/ text/de/all.po

                                        will create translated copies from each document found in graffle/src
                                        in graffle/de, using text/de/all.po for translating each document."""))
        sp.add_argument('source', type=str,
                        help='an OmniGraffle document or a folder')
        sp.add_argument('target', type=str,
                        help='target filename or folder')
        sp.add_argument('translations', type=str,
                        help='a po-file or a folder')
        # sp.add_argument('language', type=str,
        #                 help='two-digit language identifier')
        OmniGraffleSandboxedTranslator.add_verbose(sp)
        sp.set_defaults(func=OmniGraffleSandboxedTranslator.cmd_translate)


def main():
    translator = OmniGraffleSandboxedTranslator()
    translator.args.func(translator)


if __name__ == '__main__':
    main()
