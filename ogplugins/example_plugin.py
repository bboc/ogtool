"""
Example plugin for ogtools, lists document canvases and contents of config file.

To run:

$ ogtool run-plugin example_plugin ./tests/color-test.graffle  ogplugins/example_plugin.yaml --canvas my-canvas -vvv
"""


def main(document, config, canvas=None, verbose=None):
    print 'example plugin'
    print "canvas", canvas
    print 'verbose', verbose
    print "canvases in document:"
    for c in document.canvases():
        print c.name()

    print repr(config)
