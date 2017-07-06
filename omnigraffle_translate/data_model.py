#!/usr/bin/env python
"""
The OmniGraffle document data model.

Incomplete for now, because wit's unclear where the tables are hidden).

TODO: where are the tables hidden (are they groups, or subgraphs)
TODO: look at html docs

use the walk methond of Item with a test document to see what is actually in the test documents


"""


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

     def walk(self):
     	"""Traverse the a document tree (start with a canvas."""
     	print self.__class__.__name__
     	if isinstance(self, Named):
     		print self.item.Named
     	if isinstance(a, TextContainer):
     		print self.item.text
 		for klass in self.elements:
 			collection = getattr(self.item, klass.collection)
 			for item in collection:
 				i = klass(item)
 				i.walk()


class Named(object):
    has_name = True


class TextContainer(object):
    contains_text = True


class Canvas(Item, Named, TextContainer):
    collection = 'canvases'
    elements = [Graphic, Group, Layer, Line, Shape, Solid, Subgraph]


class Column(Item):
	collection = 'columns'
 	elements = [Group] # TODO: what else??


class Graphic(Item):  # Group, Line, Solid
    elements = [IncomingLine, Line, OutgoingLine ] # TODO: also contains "user data items, what is that?"


class Group(Item): 
    elements = [Graphic, Group, Shape, Solid, Subgraph]
    collection = 'groups'


class Label(Item, TextContainer):
    collection = 'labels'


class Layer(Item):
	collection = 'layers'
	elements = [Graphic, Group, Line, Shape, Solid, Subgraph]


class Line(Item):
    collection = 'lines'
    elements = [Label]


class IncomingLine(Line):
    collection = 'incoming_lines'


class OutgoingLine(Line):
    collection = 'outgoing_lines'


class Row(Item):
	collection = 'rows' 
	elements = [Group, Graphic] # TODO: what else??


class Shape(Item, TextContainer):
	collection = 'shapes'


class Solid(Item, TextContainer): # Polygon, Shape
	collection = 'solids'


class Subgraph(object):
	collection = 'subgraphs'
	elements = [Graphic, Group, Shape, Solid, Subgraph]


class TableSlice(Item):
	"""A row or column of a table."""
	collection = 'table_slices'
	elements = [Group] # TODO: what else??

