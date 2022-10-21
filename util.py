from lxml import etree as ET
import csv
import inspect
import logging
import subprocess


# https://stackoverflow.com/questions/18159221/remove-namespace-and-prefix-from-xml-in-python-using-lxml
def remove_namespace(doc, namespace):
    """Remove namespace in the passed document in place."""
    ns = "{%s}" % namespace
    nsl = len(ns)
    for elem in doc.iter():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]


# https://stackoverflow.com/questions/4624062/get-all-text-inside-a-tag-in-lxml
def stringify_children(node):
    s = node.text
    if s is None:
        s = ""
    for child in node:
        print(child)
        # s += ET.tostring(child, encoding='unicode')
        buf = child.text
        if buf:
            s += buf
    print(s)
    return s


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


def get_xpaths(tsv_file):
    xpath = {}
    with open(tsv_file) as f:
        read_tsv = csv.reader(f, delimiter="\t")
        next(read_tsv)
        for row in read_tsv:
            # print(row)
            xpath[row[0]] = row[1]
            # print(f"    def {row[0]}(self):")
            # print(f'        xpath("{row[1]}")')
            # print()
    return xpath


def get_methods(obj):
    methods = {}

    for attr_name in sorted(dir(obj)):
        attr_val = getattr(obj, attr_name)

        if attr_name.startswith("_") or not callable(attr_val):
            continue

        if len(inspect.signature(attr_val).parameters) > 0:
            continue

        methods[attr_name] = attr_val

    return methods


def clean_text(text):
    return " ".join(text.split()).strip()


