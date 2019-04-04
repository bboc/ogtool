# OmniGraffle Tool (ogtool)


A set of command-line tools for [OmniGraffle 6+](http://www.omnigroup.com/products/omnigraffle/), for export, translation, replacement of fonts and colors etc. Comes with a plugin API to that allows for simple manipulation of items in OmniGraffle documents.

There is a port of _ogtool_ to JXA, which is a [work in progress](https://github.com/bboc/omnigraffle-tools/).

Included commands:

- **ogexport**: exporting of OmniGraffle canvases to bmp, eps, gif, jpg, png, pdf, psd (Photoshop), tiff, vdx (Visio XML). Not yet supported: html, SVG. OmniGraffle's export settings can be overridden, those settings can conveniently be stored in a settings file. 
- **ogtranslate**: ogtranslate implements a full translation workflow for OmniGraffle files, extracting tests to gettext pot-files, and injecting translated texts from PO-files into a separate copy of the OmniGraffle document
for each language.
- **ogtool** implements a plugins to inspect and manipulate OmniGraffle documents, with a simple way to traverse the element tree, and configuration in YAML files. Included are example plugins, e.g. for updating fonts and colors on a set of design documents.


This software is based on [omnigraffle_export](https://github.com/fikovnik/omnigraffle-export) created and maintained by [Filip Krikava](https://github.com/fikovnik). omnigraffle_export is still included in this repository, as it contains some features ogtool does not (and probably will never) support, see the [documentation for omnigraffle_export](ommigraffle_export.md) for more details.


## Installation

ogtool is running on OS-X and requires the following: 

-   [OmniGraffle](http://www.omnigroup.com/mailman/archive/omnigraffle-users/2008/004785.html) 5 or 6
-   python \>= 2.7
-   [appscript](http://appscript.sourceforge.net/py-appscript/index.html) \>= 0.22

To install it, clone the repository and use the setup tool:

    $ setup.py install

or

    $ make install


## Usage: ogexport

Command-line tool for exporting OmniGraffle 6 files to (almost) all supported file formats (HMTL and SVG currently disabled). Supports export of one specific canvas, or all canvases in a file. 

Scale, resolution and transparency can be set via optional parameters.
    
    usage: ogexport [-h] [--canvas CANVAS] [--scale SCALE]
                    [--resolution RESOLUTION] [--transparent] [--verbose]
                    format source target
    
    Export canvases from OmniGraffle 6.
    
    positional arguments:
      format                Export formats: bmp, eps, gif, jpg, png, pdf, psd
                            (Photoshop), tiff, vdx (Visio XML) (not supported:
                            html, svg)
      source                an OmniGraffle file
      target                folder to export to
    
    optional arguments:
      -h, --help            show help message and exit
      --canvas CANVAS       export canvas with given name
      --scale SCALE         The scale to use during export (1.0 is 100%)
      --resolution RESOLUTION
                            The number of pixels per point in the resulting
                            exported image (1.0 for 72 DPI)
      --transparent         export with transparent background
      --verbose, -v
   
If a file fails, simply try again. Export uses current export settings stored in OmniGraffle for each filetype, except for those explicitly overridden through arguments. Overridden export settings are restored to previous values in OmniGraffle after export. Arguments can be read from a file, filename needs to be prefixed with @ on the command-line. In config files, use one argument per line (e.g. --resolution=1.0).

### Example

Export the canvas "my Canvas" in foobar.graffle to png to the folder `png` using the export settings stored in `140dpi-transp.ini`

    $ ogexport --canvas "my Canvas" png foobar.graffle png/ @140dpi-transp.ini

140dpi-transp.ini:

    --resolution=1.94444441795
    --scale=1.0
    --transparent

Export all OmniGraffle documents in a folder:

    $ ls -b src | xargs -I {} ogexport png "src/{}" png/140dpi @140dpi.ini


## Usage: ogtranslate
  
ogtranslate implements a full translation workflow for OmniGraffle files: 

- extract all texts from an OmniGraffle document and store them in a gettex pot-file for translation, e.g. though [Poedit](http://poedit.net) or a translation platform like [Crowdin](http://crowdin.com)
- inject translated texts from a po-file into a copy of the OmniGraffle document

In the future, ogtranslate will also support injecting new or updated translations into OmniGraffle files that have been updated (e.g. with new font sizes or other corrections necessary for a given target language).


    usage: ogtranslate [-h] [--verbose] {extract,list,translate} ...
    
    Translate canvases in OmniGraffle 6.

    positional arguments:
      {extract,list,translate}
        extract             Extract a POT file from an Omnigraffle document.
        list                List canvases in a file.
        translate           Translate an Omnigraffle document with strings from a
                            po file.

    optional arguments:
      -h, --help            show help message and exit
      --verbose, -v


### Example

Extract all texts from foobar.graffle into foobar.pot.

    $ ogtranslate extract  foobar.graffle

Inject German translations in foobar-de.po into foobar-de.graffle:

    $ ogtoool tranlsate foobar.graffle de foobar-de.po


## Usage: ogtool

Manipulate data in Omnigraffle documents. Currently comes with two fixed commands (`dump` for dumping a list of all colors and fonts used in document, see [example-output.html](example-output.html) for details, and `replace`, which replaces colors and fonts in documents based on a yaml-file), and `run-plugin` to run custom code on the element tree of an OmniGraffle document. Use `ogtool list` to see a list of all available plugins.

    usage: ogtool [-h] {dump,replace,run-plugin} ...
    
    positional arguments:
      {dump,replace,run-plugin}
        dump                Dump a list of all colors and fonts in an Omnigraffle
                            document.
        replace             Replace some fonts and / or colors in an OmniGraffle
                            document.
        run-plugin          Run a plugin on a copy of an OmniGraffle document .
    
    optional arguments:
      -h, --help            show this help message and exit


### Examples

collect all colors and fonts used in all OmniGraffle documents located in `src/` and combine the results into one html file.

    $ ls -b src | xargs -I {} ogtool dump "src/{}" -v
    $ ogtool run-plugin combine_colors_and_fonts dummy.graffle config.yaml
    $ rm  dummy-combine_colors_and_fonts.graffle

ogtools requires an OmniGraffle document to run, and will automatically create a copy for manipulation, the filename exteded by the name of the plugin used. In the case of `run-plugin combine_colors_and_fonts` the document is not required, the resulting copy can be removed. `config.yaml` would in this case contain a list of the filenames of the yaml output files generated by `ogtool dump`. 


## Plugins for ogtool

Plugins a are Python modules in the folder `ogplugins`. The first line of the module's docstring is the description output by `ogtool list`, the name of the file is the name of the plugin as required by `ogtool run-plugin`. 

Each plugin must implement a method `main(document, config, canvas=None, verbose=None)`, ogtool automatically creates a copy of the OmniGraffle document and hands in the copy as parameter document. The config is read from a yaml file and handed in a s a python data structure. 

Take a look at the example plugins _list_nodes_ and _combine_colors_and_fonts_ to see how to traverse the canvases in the document using the walk() method of  `omnigraffle.data_model.Item` and extract or manipulate data with a custom callable.

## Known Issues

1. **og-tools cannot access objects shared layers properly**. It appeared that this might be caused by py-appscript. Since py-appscript is unmaintained for quite a few years now, this issue will most likely not be fixed anytime soon. An effective workaround might be toggling the shared layers before and after processing, either manually, or maybe through AppleScript/JavsScript or even with py-appscript. **It appears now that this issue is still present when accessing OmniGraffle through JXA**
2. **ogtranslate currently does not translate line labels.** I will address this in a later version
3. **ogtools test suite is incomplete** The test suite only covers omnigraffle_export and ogexport, and needs to be extended for ogtool and ogtranslate. _I need to figure an elegant way to write tests for my JXA code._
4. **replacing text in attribute runs does not result in the document being marked as updated**, so injected tranlsations are not saved. The code contains a workaround - adding a timestamp to key 'upd_timestamp' in user data of the element containing the text - so that the element with replaced text is marked as updated. This problem is at least present in OmniGraffle 6.6.2 and can be observed through watching document.modified(). This does not only affect attribute runs, I also observed this when changing colors, user_names and font size. According to the OmniGraffle developers this behaviour has not changed in version 7. 
5. **py-appscript is no longer maintained** Maybe [py-applescript](https://pypi.org/project/py-applescript/) is a way forward, because the last commit is about a year old.

TODOs, including other small issues and more notes are tracked in [TODO.taskpaper](TODO.taskpaper)

## Links

* [PyObjC](https://bitbucket.org/ronaldoussoren/pyobjc/)
* [ASDictionary](http://appscript.sourceforge.net/tools.html#asdictionary) exports application dictionaries in plain text and HTML formats

