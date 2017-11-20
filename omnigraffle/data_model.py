#!/usr/bin/env python
"""
The OmniGraffle document data model, for traversing all elements in the
document, e,g, to extract or inject text.
"""
from __future__ import print_function

from functools import partial
import logging
import appscript


def debug(level, *args):
    msg = "|   " * level + " ".join(args)
    logging.debug(msg)


class Item(object):
    """
    An item in an OmniGraffle document.

    May be Named and/or a TextContainer.
    """
    # children = []
    _current_canvas_name = ''

    def __init__(self, item):
        self.item = item

    def walk(self, callback, skip_invisible_layers=False, nodes_visited=None, level=0):
        """
        Traverse the a document tree and invoke callback on each element.
        # TODO: apparently some items are visited more than once, others are never visited
        """
        debug = partial(globals()['debug'], level)

        # prevent visited nodes from being visited again:
        if not nodes_visited:
            nodes_visited = set()  # init not cache
        try:
            if self.item.id() in nodes_visited:
                return
            else:
                nodes_visited.add(self.item.id())
        except appscript.reference.CommandError:
            pass  # items without id cannot be tracked

        if isinstance(self, Canvas):
            debug("\n\n-----------------Canvas: '%s'-----------------\n" % self.item.name())
            Item._current_canvas_name = self.item.name()
        if isinstance(self, Layer):
            debug("\n\n---Layer: '%s'---\n" % self.item.name())
            if skip_invisible_layers and not self.item.visible():
                debug("\n...skipped invisible layer ...\n")
                return  # skip invisible layers

        debug('::::', self.info)

        # import pdb; pdb.set_trace()

        callback(self)

        for child_class in self.children:
            debug('child class', child_class)
            klass = globals()[child_class]
            collection = getattr(self.item, klass.collection_name)
            try:
                collection()
            except appscript.reference.CommandError:
                debug("\n...skipped collection", child_class)
                # apparently there's a problem with some collections, e.g. 'IncomingLine' in Graphics
                continue
            try:
                size = len(collection())
            except TypeError:  # the size of some collections cannot be determined
                debug("+--- processing collection", child_class, "size: (not available)")
            else:
                debug("+--- processing collection", child_class, "size: %s" % size)
                for idx, item in enumerate(collection()):
                    debug("   ", child_class, "# %s" % idx)
                    i = klass(item)
                    i.walk(callback, skip_invisible_layers, nodes_visited, level + 1)

    @property
    def info(self):
        return "(%s) %s == %s (%s...)" % (self.id, self.class_, self.name, self.text[:20])

    @property
    def canvas_name(self):
        # this is not thread-safe!
        return Item._current_canvas_name

    @property
    def properties(self):
        # this is not thread-safe!
        return self.item.properties()

    @properties.setter
    def properties(self, value):
        self.item.properties.set(value)

    @property
    def class_(self):
        try:
            return self.item.class_()
        except appscript.reference.CommandError:
            return None

    @property
    def id(self):
        try:
            return self.item.id()
        except appscript.reference.CommandError:
            return 'no id'

    @property
    def text(self):
        try:
            return self.item.text()
        except appscript.reference.CommandError:
            return ''

    @text.setter
    def text(self, value):
        self.item.text.set(value)

    @property
    def name(self):
        try:
            return self.item.name()
        except appscript.reference.CommandError:
            return ''

    @name.setter
    def name(self, value):
        self.item.name.set(value)


class Named(object):
    pass


class Filled(object):
    @property
    def fill_color(self):
        try:
            return self.item.fill_color()
        except appscript.reference.CommandError:
            logging.debug("Item has not fill color: %s" % self.info)
            return None

    @fill_color.setter
    def fill_color(self, value):
        self.item.fill_color.set(value)


class HasStroke(object):
    @property
    def stroke_color(self):
        try:
            return self.item.stroke_color()
        except appscript.reference.CommandError:
            logging.debug("Item has not stroke color: %s" % self.info)
            return None

    @stroke_color.setter
    def stroke_color(self, value):
        self.item.stroke_color.set(value)


class TextContainer(object):
    @property
    def text_color(self):
        return self.item.text.color()

    @text_color.setter
    def text_color(self, value):
        self.item.text.color.set(value)

    @property
    def text_font(self):
        return self.item.text.font()

    @text_font.setter
    def text_font(self, value):
        self.item.text.font.set(value)

    @property
    def text_size(self):
        return self.item.text.size()

    @text_size.setter
    def text_size(self, value):
        self.item.text.size.set(value)


class Document(Item):
    children = ['Canvas']


class Canvas(Item, Named):
    collection_name = 'canvases'
    children = ['Layer', 'Subgraph', 'Group', 'Line', 'Shape', 'Solid', 'Graphic']
    # children = ['Layer'] # TODO: are all objects in layers?


class Layer(Item):
    collection_name = 'layers'
    children = ['Subgraph', 'Group', 'Line', 'Shape', 'Solid', 'Graphic']


class TableSlice(Item):
    """A row or column of a table."""
    collection_name = 'table_slices'
    children = ['Group']  # TODO: what else?'?


class Column(Item):
    collection_name = 'columns'
    children = ['Group']  # TODO: what else?'?


class Row(Item):
    collection_name = 'rows'
    children = ['Group', 'Graphic']  # TODO: what else?'?


class Graphic(Item, HasStroke, TextContainer):  # Group', 'Line', 'Solid
    collection_name = 'graphics'
    children = ['IncomingLine', 'OutgoingLine', 'Line']  # TODO: also contains "user data items', 'what is that?'"


class Group(Graphic):
    collection_name = 'groups'
    # TODO: graphics might be enough to enumerate, subgraphs and tables are also groups
    children = ['Subgraph', 'Group', 'Shape', 'Solid', 'Graphic']


class IncomingLine(Graphic):
    collection_name = 'incoming_lines'


class Line(Graphic):
    collection_name = 'lines'
    children = ['Label']


class OutgoingLine(Graphic):
    collection_name = 'outgoing_lines'


class Solid(Graphic, Filled, TextContainer):  # Polygon', 'Shape
    collection_name = 'solids'


class Shape(Solid, Named):
    collection_name = 'shapes'


class Label(Shape, Named):
    collection_name = 'labels'


class Subgraph(Group):
    collection_name = 'subgraphs'
    children = ['Group', 'Shape', 'Solid', 'Subgraph', 'Graphic']


class Table(Group):
    collection_name = 'tables'
    children = ['Column', 'Row']
