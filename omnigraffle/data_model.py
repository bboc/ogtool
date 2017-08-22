#!/usr/bin/env python
"""
The OmniGraffle document data model, for traversing all elements in the
document, e,g, to extract or inject text.
"""

import appscript


class Item(object):
    """
    An item in an OmniGraffle document.

    May be Named and/or a TextContainer.
    """
    elements = []
    _current_canvas_name = ''

    def __init__(self, item):
        self.item = item

    def walk(self, callable, skip_invisible_layers=True):
        """
        Traverse the a document tree and call a method on each element.
        # TODO: apparently some elements are visited more than once, others are never visited
        """
        if isinstance(self, Canvas):
            Item._current_canvas_name = self.item.name()
        if skip_invisible_layers:
            if isinstance(self, Layer) and self.item.visible():
                return  # skip invisible layers
        callable(self)

        for ix, class_name in enumerate(self.elements):
            klass = globals()[class_name]
            collection = getattr(self.item, klass.collection)
            try:
                for idx, item in enumerate(collection()):
                    i = klass(item)
                    i.walk(callable, skip_invisible_layers)
            except appscript.reference.CommandError:
                pass  # TODO: when does this happen, can we avoid this?
            except TypeError:
                pass  # no elements TODO: this is hacky

    @property
    def canvas_name(self):
        return Item._current_canvas_name

    @property
    def properties(self):
        return self.item.properties()

    @properties.setter
    def properties(self, value):
        self.item.properties.set(value)


class Named(object):
    @property
    def name(self):
        return self.item.name()

    @name.setter
    def name(self, value):
        self.item.name.set(value)


class Filled(object):
    @property
    def fill_color(self):
        return self.item.fill_color()

    @fill_color.setter
    def fill_color(self, value):
        self.item.fill_color.set(value)


class HasStroke(object):
    @property
    def stroke_color(self):
        return self.item.stroke_color()

    @stroke_color.setter
    def stroke_color(self, value):
        self.item.stroke_color.set(value)


class TextContainer(object):
    @property
    def text(self):
        return self.item.text

    @text.setter
    def text(self, value):
        self.item.text.set(value)


class Document(Item):
    elements = ['Canvas']


class Canvas(Item, Named):
    collection = 'canvases'
    # TODO: are all objects in layers?
    elements = ['Graphic', 'Group', 'Layer', 'Line', 'Shape', 'Solid', 'Subgraph']


class Layer(Item):
    collection = 'layers'
    elements = ['Graphic', 'Group', 'Line', 'Shape', 'Solid', 'Subgraph']


class TableSlice(Item):
    """A row or column of a table."""
    collection = 'table_slices'
    elements = ['Group']  # TODO: what else?'?


class Column(Item):
    collection = 'columns'
    elements = ['Group']  # TODO: what else?'?


class Row(Item):
    collection = 'rows'
    elements = ['Group', 'Graphic']  # TODO: what else?'?


class Graphic(Item, HasStroke):  # Group', 'Line', 'Solid
    collection = 'graphics'
    elements = ['IncomingLine', 'Line', 'OutgoingLine']  # TODO: also contains "user data items', 'what is that?'"


class Group(Graphic):
    # TODO: graphics might be enough to enumerate, subgraphs and tables are also groups
    elements = ['Graphic', 'Group', 'Shape', 'Solid', 'Subgraph']
    collection = 'groups'


class IncomingLine(Graphic):
    collection = 'incoming_lines'


class Line(Graphic):
    collection = 'lines'
    elements = ['Label']


class OutgoingLine(Graphic):
    collection = 'outgoing_lines'


class Solid(Graphic, Filled, TextContainer):  # Polygon', 'Shape
    collection = 'solids'


class Shape(Solid, Named):
    collection = 'shapes'


class Label(Shape, Named):
    collection = 'labels'


class Subgraph(Group):
    collection = 'subgraphs'
    elements = ['Graphic', 'Group', 'Shape', 'Solid', 'Subgraph']


class Table(Group):
    collection = 'tables'
    elements = ['Column', 'Row']
