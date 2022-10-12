from lxml import etree as ET
import time

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
