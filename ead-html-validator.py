#!/usr/bin/env python3

from bs4 import BeautifulSoup
#from xml.etree import ElementTree as ET
from lxml import etree as ET

import argparse
import csv
import logging
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
parser.add_argument("html_file", metavar="HTML_FILE",
    help="html file")
parser.add_argument("-d", "--debug",
    help="Enable debugging messages", action="store_true")
args = parser.parse_args()

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

logging.debug("ead file: %s", args.ead_file)
logging.debug("htmlt file: %s", args.html_file)

validate(args.ead_file)

nsmap = {"e": "urn:isbn:1-931666-22-9"}

tree = ET.parse(args.ead_file)
logging.debug(tree)
root = tree.getroot()
logging.debug(root)
remove_namespace(root, nsmap['e'])
logging.debug(root)

logging.debug(root.tag)

soup = BeautifulSoup(open(args.html_file), 'html.parser')

find_text = ET.XPath("//text()")

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
    print(results

    if not results:
        num_err += 1
        logging.warning(f"can't find {field} in html")
        continue

    exit(1)

