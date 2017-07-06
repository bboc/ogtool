#!/usr/bin/env python
"""
The OmniGraffle document data model.

Incomplete for now, because wit's unclear where the tables are hidden).

TODO: where are the tables hidden (are they groups, or subgraphs)
TODO: look at html docs

use the walk methond of Item with a test document to see what is actually in the test documents


"""

import appscript 
class Item(object):
    """
    An item in an OmniGraffle document.

    May be Named and/or a TextContainer.
    """
    elements = []
    def __init__(self, item):
        self.item = item
        self.has_name = False 
        self.contains_text = False

    def walk(self, file_name, canvas_name, memory):
        """Traverse the a document tree (start with a canvas."""
        if isinstance(self, Layer) and self.item.visible():
            return # skip invisible laters
        if isinstance(self, Named):
          pass
        if isinstance(self, TextContainer):
            # add text to memory
            memory[self.item.text()] = "#: %s/%s:%s\n" % (file_name, canvas_name, self.item.id())

        for ix, class_name in enumerate(self.elements):
            klass = globals()[class_name]
            collection = getattr(self.item, klass.collection)
            try: 
                for idx, item in enumerate(collection()):
                    i = klass(item)
                    i.walk(file_name, canvas_name, memory)
            except appscript.reference.CommandError:
                pass # print 'caught appscript.reference.CommandError'
            except TypeError:
                pass # print prefix , 'no elements'


class Named(object):
    has_name = True


class TextContainer(object):
    contains_text = True


class Canvas(Item, Named):
    collection = 'canvases'
    elements = ['Graphic', 'Group', 'Layer', 'Line', 'Shape', 'Solid', 'Subgraph']


class Column(Item):
    collection = 'columns'
    elements = ['Group'] # TODO: what else?'?


class Graphic(Item):  # Group', 'Line', 'Solid
    collection = 'graphics'
    elements = ['IncomingLine', 'Line', 'OutgoingLine'] # TODO: also contains "user data items', 'what is that?'"


class Group(Item): 
    elements = ['Graphic', 'Group', 'Shape', 'Solid', 'Subgraph']
    collection = 'groups'


class Label(Item, TextContainer):
    collection = 'labels'


class Layer(Item):
    collection = 'layers'
    elements = ['Graphic', 'Group', 'Line', 'Shape', 'Solid', 'Subgraph']


class Line(Item):
    collection = 'lines'
    elements = ['Label']


class IncomingLine(Line):
    collection = 'incoming_lines'


class OutgoingLine(Line):
    collection = 'outgoing_lines'


class Row(Item):
    collection = 'rows' 
    elements = ['Group', 'Graphic'] # TODO: what else?'?


class Shape(Item, TextContainer):
    collection = 'shapes'


class Solid(Item, TextContainer): # Polygon', 'Shape
    collection = 'solids'


class Subgraph(object):
    collection = 'subgraphs'
    elements = ['Graphic', 'Group', 'Shape', 'Solid', 'Subgraph']


class TableSlice(Item):
    """A row or column of a table."""
    collection = 'table_slices'
    elements = ['Group'] # TODO: what else?'?

