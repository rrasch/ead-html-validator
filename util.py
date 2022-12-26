from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from dateutil.parser import parse, ParserError
from lxml import etree as ET
from pprint import pprint, pformat
from resultset import ResultSet
from urllib.parse import urlparse
import csv
import inspect
import logging
import re
import requests
import string
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
        logging.debug(child)
        # s += ET.tostring(child, encoding='unicode')
        buf = child.text
        if buf:
            s += buf
    logging.debug(s)
    return s


def do_cmd(cmdlist, allowed_returncodes=None, **kwargs):
    cmd = list(map(str, cmdlist))
    logging.debug("Running command: %s", " ".join(cmd))

    ok_returncodes = [0]
    if allowed_returncodes:
        ok_returncodes.extend(allowed_returncodes)

    process = None
    try:
        process = subprocess.run(
            cmd, check=False, universal_newlines=True, **kwargs
        )
    except subprocess.CalledProcessError as e:
        logging.exception(e)
    except Exception as e:
        logging.exception(e)

    if process and process.returncode in ok_returncodes:
        return process
    else:
        return None


def get_xpaths(tsv_file):
    xpath = {}
    with open(tsv_file) as f:
        read_tsv = csv.reader(f, delimiter="\t")
        next(read_tsv)
        for row in read_tsv:
            # logging.debug(row)
            xpath[row[0]] = row[1]
            # logging.debug(f"    def {row[0]}(self):")
            # logging.debug(f'        xpath("{row[1]}")')
            # logging.debug()
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
    text = re.sub(r"\s+", " ", text)
    # text = re.sub(r'\s([?.!"](?:\s|$))', r'\1', text)
    text = re.sub(
        rf"\s([{re.escape(string.punctuation)}](?:\s|$))", r"\1", text
    )
    text = text.strip()
    return text


def clean_text2(text):
    return " ".join(text.split()).strip()


def resolve_handle(url):
    response = requests.get(url, allow_redirects=False)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.a["href"]

def strip_date(title):
    title_list = title.rsplit(":", 1)
    if len(title_list) == 1:
        return title
    try:
        date = parse(title_list[1])
        return title_list[0]
    except ParserError as e:
        return title

def get_links(html_file):
    soup = BeautifulSoup(open(html_file), "html.parser")
    link = soup.find("link", rel="canonical")
    base_url = ""
    if link:
        url = urlparse(link["href"])
        base_url = f"{url.scheme}://{url.netloc}"

    links = set()
    for a in soup.find_all("a"):
        link = a["href"]
        if link.startswith("#"):
            continue
        if link.startswith("/"):
            link = f"{base_url}{link}"
        links.add(link)

    return (list(links))


def find_broken_links(links):

    # Internal function for validating HTTP status code.
    def _validate_url(url):
        r = requests.head(url)
        if r.status_code == 404:
            broken_links.append(url)

    broken_links = []
    # Loop through links checking for 404 responses, and append to list.
    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(_validate_url, links)

    return broken_links

def sort_dict(mydict):
    return dict(sorted(mydict.items(), key=lambda item: item[1]))


def xpath(root, expr, all_text=False, join_text=False, sep=" "):
    attrib = None
    match = re.search(r"(/@([A-Za-z]+))$", expr)
    if match:
        attrib = match.group(2)
        expr = re.sub(rf"{match.group(1)}$", "", expr)

    nodes = root.xpath(expr)
    if not nodes:
        return None

    total_text = ""
    result = ResultSet(xpath=expr)
    for node in nodes:
        if attrib:
            text = node.get(attrib)
            if text is None:
                continue
        elif all_text:
            words = []
            for itext in node.itertext():
                # words.extend(itext.split())
                words.append(itext)
            text = clean_text(sep.join(words))
        else:
            text = clean_text(node.text or "")
        if join_text:
            total_text += " " + text
        else:
            result.add(node.tag, text, node.sourceline)

    if join_text:
        result.add(nodes[0].tag, total_text[1:], nodes[0].sourceline)

    return result if not result.isempty() else None

def quote(val):
    if type(val) == str:
        return f"'{val}'"
    else:
        return str(val)

def create_args_str(*args, **kwargs):
    sep = ", "
    arg_str = sep.join([quote(a) for a in args])
    kw_str =  sep.join([f"{k}={quote(kwargs[k])}" for k in kwargs.keys()])

    if arg_str and kw_str:
        return arg_str + sep + kw_str
    elif arg_str:
        return arg_str
    else:
        return kw_str

# https://stackoverflow.com/a/35804945/1691778
def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError(
            "{} already defined in logging module".format(levelName)
        )
    if hasattr(logging, methodName):
        raise AttributeError(
            "{} already defined in logging module".format(methodName)
        )
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError(
            "{} already defined in logger class".format(methodName)
        )

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)
