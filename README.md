# ead-html-validator

## About ##

ead-html-validator is a command line tool that validates a set
of Finding Aids HTML files generated by Hugo.  The HTML is
deemed valid if the content of an ArchiveSpace EAD appears
within the HTML files. Please reference JIRA ticket FADESIGN-230
for more information.

## Requirements ##

ead-html-validator requires Python >= 3.7 and depends on the
following modules:

- anytree
- beautifulsoup4
- inflect
- pycountry
- python-dateutil
- python-Levenshtein
- requests
- lxml
- tomli
- tqdm
- thefuzz

## Installation

Make sure you have Python version 3.7 or greater. If Python is
already present on your system, you can confirm the version by
running Python with the `-V` or `--version` option. For example
the following shows the output for a sytem with version 3.9:

```
$ python3 -V
Python 3.9.16
```

The following [document](Install-Python.md) provides some direction for installing Python on various
operating systems: [Install-Python.md](Install-Python.md)

Next checkout validator repository on github:

```
$ cd ~
$ git clone https://github.com/rrasch/ead-html-validator.git
```

Set up a virtual environment.  For example, to create one in
your home directory:

```
$ mkdir ~/venv
$ cd ~/venv
$ python3 -m venv ead-html-validator
$ source ead-html-validator/bin/activate
$ pip3 install .
```

Test out the script:

```
$ ead-html-validator.py
usage: ead-html-validator.py [-h] [--diff-type {color,unified,unified-color,simple}] [-v] [-l LOG_FORMAT] [-t] [-i]
                             [--indent-dir INDENT_DIR] [-b] [-c] [-p] [-e] [--html-parser {html.parser,html5lib}] [-m]
                             [--threading] [--duration]
                             EAD_FILE HTML_DIR
ead-html-validator.py: error: the following arguments are required: EAD_FILE, HTML_DIR
```

To exit the virtual environment:

```
$ deactivate
```

## Usage ##

The tools takes in two arguments:

- the path to an EAD xml file
- the path to a directory containing HTML files

The command line looks like the following

```
ead-html-validator.py <ead_xml_file> <finding_aids_html_dir>
```

## Debugging

Add the -d switch for debugging output
