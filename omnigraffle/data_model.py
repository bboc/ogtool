#!/usr/bin/env python
"""
The OmniGraffle document data model, for traversing all elements in the 
document, e,g, to extract or inject text.

Incomplete for now, because it's unclear where the tables are hidden.

TODO: where are the tables hidden (are they groups, or subgraphs)
TODO: look at html docs


document > canvas 
canvas > graphics 
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

    @property
    def properties(self):
        return self.item.properties()

    @properties.setter
    def properties(self, value):
        self.item.properties.set(value)


class Named(object):
    has_name = True


class Canvas(Item, Named):
    collection = 'canvases'
    elements = ['Graphic', 'Group', 'Layer', 'Line', 'Shape', 'Solid', 'Subgraph']


class Column(Item):
    collection = 'columns'
    elements = ['Group'] # TODO: what else?'?


class Graphic(Item):  # Group', 'Line', 'Solid
    collection = 'graphics'
    elements = ['IncomingLine', 'Line', 'OutgoingLine'] # TODO: also contains "user data items', 'what is that?'"

    @property
    def stroke_color(self):
        return self.item.stroke_color()

    @stroke_color.setter
    def stroke_color(self, value):
        self.item.stroke_color.set(value)



class Group(Graphic): 
    # TODO: graphics might be enough to enumerate, subgraphs and tables are also groups
    elements = ['Graphic', 'Group', 'Shape', 'Solid', 'Subgraph']
    collection = 'groups'


class Label(Shape):
    collection = 'labels'


class Layer(Item):
    collection = 'layers'
    elements = ['Graphic', 'Group', 'Line', 'Shape', 'Solid', 'Subgraph']


class Line(Graphic):
    collection = 'lines'
    elements = ['Label']


class IncomingLine(Graphic):
    collection = 'incoming_lines'


class OutgoingLine(Graphic):
    collection = 'outgoing_lines'


class Row(Item):
    collection = 'rows' 
    elements = ['Group', 'Graphic'] # TODO: what else?'?


class Shape(Solid, Named):
    collection = 'shapes'


class Solid(Graphic, TextContainer): # Polygon', 'Shape
    collection = 'solids'

    @property
    def text(self):
        return self.item.text()

    @text.setter
    def fill_color(self, value):
        self.item.text.set(value)

    @property
    def fill_color(self):
        return self.item.fill_color()

    @fill_color.setter
    def fill_color(self, value):
        self.item.fill_color.set(value)


class Subgraph(Group):

    collection = 'subgraphs'
    elements = ['Graphic', 'Group', 'Shape', 'Solid', 'Subgraph']


class Table(Group):
    collection = 'tables'
    elements = [''Column', 'Row']


class TableSlice(Item):
    """A row or column of a table."""
    collection = 'table_slices'
    elements = ['Group'] # TODO: what else?'?

