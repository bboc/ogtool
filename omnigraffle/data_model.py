#!/usr/bin/env python
"""
The OmniGraffle document data model, for traversing all elements in the 
document, e,g, to extract or inject text.

Incomplete for now, because it's unclear where the tables are hidden.

TODO: where are the tables hidden (are they groups, or subgraphs)
TODO: look at html docs

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

    def walk(self, callable):
        """
        Traverse the a document tree and call a method on each element.
        # TODO: apparently some elements are visited more than once/
        """
        
        if isinstance(self, Layer) and self.item.visible():
            return # skip invisible laters
        callable(self)

        for ix, class_name in enumerate(self.elements):
            klass = globals()[class_name]
            collection = getattr(self.item, klass.collection)
            try: 
                for idx, item in enumerate(collection()):
                    i = klass(item)
                    i.walk(callable)
            except appscript.reference.CommandError:
                pass # TODO: when does this happen, can we avoid this?
            except TypeError:
                pass # no elements TODO: this is hacky


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

