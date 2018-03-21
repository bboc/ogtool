import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="ogtool",
    version="0.5.2",
    packages=find_packages(exclude='tests'),
    install_requires=['appscript', 'pyobjc', 'polib', 'pyyaml'],
    author="Bernhard Bockelbrink, Filip Krikava (export code)",
    author_email="bernhard.bockelbrink@gmail.com",
    description="A set of commandline tools for OmniGraffle 6+, for export, translation, replacement of fonts and colors etc. Comes with a plugin API to that allows for simple manipulation of items in OmniGraffle documents.",
    long_description=read("README.md"),
    license="http://www.opensource.org/licenses/mit-license.php",
    keywords="omnigraffle export gettext i18n command",
    url="https://github.com/bboc/ogtool",
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        'Operating System :: MacOS :: MacOS X',
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities"
    ],
    entry_points={
        'console_scripts': [
            'omnigraffle-export = omnigraffle_export.omnigraffle_export:main',
            'ogexport = ogtools.export:main',
            'ogtranslate = ogtools.translate:main',
            'ogtool = ogtools.ogtool:main',
        ],
    },
    test_suite='tests',
    zip_safe=True,
)
