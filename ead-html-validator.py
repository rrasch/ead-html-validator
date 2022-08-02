#!/usr/bin/env python3

from bs4 import BeautifulSoup
#from xml.etree import ElementTree as ET
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from lxml import etree as ET

import argparse
import ead
import eadhtml
import constants
import csv
import logging
import os.path
import subprocess


# https://stackoverflow.com/questions/18159221/remove-namespace-and-prefix-from-xml-in-python-using-lxml
def remove_namespace(doc, namespace):
    """Remove namespace in the passed document in place."""
    ns = u'{%s}' % namespace
    nsl = len(ns)
    for elem in doc.iter():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]


def do_cmd(cmdlist, **kwargs):
    cmd = list(map(str, cmdlist))
    logging.debug("Running command: %s", " ".join(cmd))
    process = None
    try:
        process = subprocess.run(cmd, check=True, **kwargs)
    except subprocess.CalledProcessError as e:
        logging.exception(e)
    except Exception as e:
        logging.exception(e)
    if process and process.returncode == 0:
        return True
    else:
        return False


def validate(xml_file):
    return do_cmd(['xmllint', '--noout',
        '--schema', 'ead.xsd', xml_file])

def get_xpaths(tsv_file):
    xpath = {}
    with open(tsv_file) as f:
        read_tsv = csv.reader(f, delimiter="\t")
        next(read_tsv)
        for row in read_tsv:
            #print(row)
            xpath[row[0]] = row[1]
            #print(f"    def {row[0]}(self):")
            #print(f'        xpath("{row[1]}")')
            #print()
    return xpath

xpath = get_xpaths("ead_fields.tsv")

# for field in sorted(xpath.keys()):
#     print(field)
#     print(xpath[field])

logging.basicConfig(
    format='%(asctime)s - ead-validator - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')

parser = argparse.ArgumentParser(
    description="Validate.")
parser.add_argument("ead_file", metavar="EAD_FILE",
    help="ead file")
parser.add_argument("html_dir", metavar="HTML_DIR",
    help="html directory")
parser.add_argument("-d", "--debug",
    help="Enable debugging messages", action="store_true")
args = parser.parse_args()

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

logging.debug("ead file: %s", args.ead_file)
logging.debug("html dir: %s", args.html_dir)

validate(args.ead_file)


nsmap = {"e": "urn:isbn:1-931666-22-9"}

tree = ET.parse(args.ead_file)
logging.debug(tree)
root = tree.getroot()
logging.debug(root)
remove_namespace(root, nsmap['e'])
logging.debug(root)

logging.debug(root.tag)

my_ead = ead.Ead(args.ead_file)

for method_name in constants.EAD_FIELDS:
    method = getattr(my_ead, method_name)
    print(f"calling {method_name}()")
    val = method()
    print(f"val={val}")

print(my_ead.eadid())
print(my_ead.url())
print(my_ead.author())
print(my_ead.unittitle())
print(my_ead.unitid())
print(my_ead.langcode())
print(my_ead.language())

print(my_ead.abstract())

print(my_ead.bioghist())

print(my_ead.scopecontent())

#print(my_ead.subject())

print(my_ead.geogname())
print(my_ead.genreform())
print(my_ead.occupation())
print(my_ead.subject())


def validate_component(c, dirpath):

    print('----')
    print(c.id())
    print(c.level())
    print(c.title())
    print()

    new_dirpath = dirpath

    if (c.level() == "series"):
        new_dirpath = os.path.join(new_dirpath, "contents", c.id())

    html_file = os.path.join(new_dirpath, "index.html")
    ehtml = eadhtml.EADHTML(html_file)
    chtml = ehtml.find_component(c.id())
    print(chtml)
    print(chtml.id())
    print(chtml.level())
    print(chtml.title())
    print("extent: %s" % chtml.extent())

    for sub_c in c.sub_components():
        # print(sub_c)
        # print(sub_c.id())
        # print(sub_c.level())
        validate_component(sub_c, new_dirpath)


components = my_ead.component()

# validate_component(components[1], args.html_dir)

for c in my_ead.component():
    validate_component(c, args.html_dir)


exit()

my_ead.creator()

html_file = os.path.join(args.html_dir, 'index.html')

soup = BeautifulSoup(html_file, 'html.parser')

#find_text = ET.XPath("//text()")
#print(root.find_text)

ehtml = eadhtml.EADHTML(html_file)

print(ehtml.creator())
print(ehtml.author())
print(ehtml.abstract())
print(ehtml.unitid())
print(ehtml.bioghist())
print(ehtml.extent())

print(ehtml.arrangement())

exit()

num_err = 0

#for field in sorted(xpath.keys()):
for field in xpath.keys():
    print(field)
    print(xpath[field])
    expr = xpath[field]

    if field.startswith("unitdate"):
        continue

    if expr == "":
        continue

    #if not expr.startswith('/'):
    #    expr = 'eadheader/' + expr
    #print(expr)
    node = root.xpath(expr)
    print(node)



    print(type(node[0]).__name__)
    if isinstance(node[0], ET._Element):
        print(node[0].text)

    results = soup.find(text=node[0].text)
    print(type(results).__name__)
    print(dir(results))
    print(results)

    if not results:
        num_err += 1
        logging.warning(f"can't find {field} in html")
        continue

    exit(1)

