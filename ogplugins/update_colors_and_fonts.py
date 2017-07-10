"""
Update colors and fonts in a document (and adapt font size).
"""

from functools import partial
from omnigraffle.data_model import Document, TextContainer

def main(document, config, canvas=None, verbose=None):
    """
    Replace fonts as defined in config.yaml

    fonts:
      source-font: [replacement-font, size-delta (int)]
      OpenSans: [OpenSans-Thin, -2]
    colors:
        source-color: target-color
        03FC48: 03FC49
    """
    print repr(config)
    exit

    def replace(config, element):
        # TODO: replace colors/fill colors
        if isinstance(element, TextContainer):
            if element.item.text(): # element might still have no text
                current_font = element.text.font()
                if config['fonts'].has_key(current_font):
                    new_font, size_delta = config['fonts'][current_font]
                    size = element.text.size()
                    new_size = size + size_delta
                    element.text.size.set(new_size)
                    element.text.font.set(new_font)

    d = Document(document)
    d.walk(partial(replace, config))
