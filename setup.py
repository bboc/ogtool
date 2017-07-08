import os
from setuptools import setup, find_packages
from pkg_resources import resource_filename

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup (
    name = "omnigraffle-export",
    version = "1.7.1",
    packages = find_packages(exclude='tests'),
    install_requires = ['appscript','pyobjc', 'polib'],
    author = "Filip Krikava",
    author_email = "krikava@gmail.com",
    description = "A command line utility that exports omnigraffle canvases files into various formats.",
    long_description = read("README.md"),
    license = "http://www.opensource.org/licenses/mit-license.php",
    keywords = "omnigraffle export",
    url = "https://github.com/fikovnik/omnigraffle-export",
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        'Operating System :: MacOS :: MacOS X',
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities"
    ],
    entry_points = {
        'console_scripts': [
            'omnigraffle-export = omnigraffle_export.omnigraffle_export:main',
            'og-export = ogtools.export:main',
            'og-translate = ogtools.translate:main',
            'og-tool = ogtools.ogtool:main',
        ],
    },
    test_suite = 'tests',
    zip_safe = True,
)
