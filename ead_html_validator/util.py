from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from dateutil.parser import parse, ParserError
from dateutil.relativedelta import relativedelta
from ead_html_validator.resultset import ResultSet
from html.entities import codepoint2name
from lxml import etree as ET
from pprint import pprint, pformat
from urllib.parse import urlparse, urlsplit, urlunsplit
import csv
import inspect
import json
import logging
import os.path
import re
import requests
import string
import subprocess


class CommandFailedError(Exception):
    pass


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


def change_ext(filename, new_ext):
    basename, ext = os.path.splitext(filename)
    return f"{basename}{new_ext}"


def change_handle_scheme(*links):
    new_links = []
    for link in links:
        url_parts = list(urlsplit(link))
        if url_parts[1].endswith("handle.net"):
            url_parts[0] = "https"
        new_links.append(urlunsplit(url_parts))
    return new_links


def clean_date(date):
    date = " ".join(date.split())
    return date


def clean_date_normal(date):
    return "-".join(set(date.split("/", maxsplit=1)))


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    # text = re.sub(r'\s([?.!"](?:\s|$))', r"\1", text)
    punc = re.sub(r"[-&#<>]", "", string.punctuation)
    # strip whitespace before punctuation
    text = re.sub(rf"\s([{re.escape(punc)}](?:\s|$))", r"\1", text)

    # chars showing up in the query strings of urls
    # with the html
    text = text.replace("¬", "&not")
    text = text.replace("∣=", "&mid=")
    text = text.replace("≪=", "&ll=")

    # overescaped chars in ead xml
    text = text.replace(" &amp; ", " & ")
    text = text.replace("&gt;", ">")
    text = text.replace("&amp;amp;", "&")
    text = text.replace("&#38;", "&")
    text = text.replace("&rsquo;", "’")

    text = text.strip()
    return text


def clean_text2(text):
    return " ".join(text.split()).strip()


def create_args_str(*args, **kwargs):
    sep = ", "
    arg_str = sep.join([quote(a) for a in args])
    kw_str = sep.join([f"{k}={quote(kwargs[k])}" for k in kwargs.keys()])

    if arg_str and kw_str:
        return arg_str + sep + kw_str
    elif arg_str:
        return arg_str
    else:
        return kw_str


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
    elif process:
        print(process.stderr)
        process.check_returncode()
    else:
        raise CommandFailedError(f"Error running {cmd}")


# https://beckism.com/2009/03/named_entities_python/
def encode_named_entities(
    text, convert_less_than=False, convert_greater_than=False
):
    """Converts UTF-8 characters into HTML entities

    By default, all non-ASCII characters and ampersand will be converted to named
    entities, falling back on numeric entities.

    Less than and greater than characters can be optionally included with the
    keyword arguments.

    Returns the modified string.

    USAGE:
        text = "I love <b>jalapeños & fun</b> ☜!"
        entity_text = encode_named_entities(text)
        # "I love <b>jalape&ntilde;os &amp; fun</b> &#9756;!"
        entity_text = encode_named_entities(text, convert_less_than=True)
        # "I love &lt;b>jalape&ntilde;os &amp; fun&lt;/b> &#9756;!"
    """
    new_text_list = []
    for character in text:
        code_point = ord(character)
        # ASCII characters are 0-127
        if code_point < 128:
            # Process ampersands and carets, if requested
            if character == "&":
                new_text_list.append("&amp;")
            elif character == "<" and convert_less_than:
                new_text_list.append("&lt;")
            elif character == ">" and convert_greater_than:
                new_text_list.append("&gt;")
            else:
                new_text_list.append(character)
        else:
            # For all other characters, try to convert to named entity
            try:
                new_text_list.append(f"&{codepoint2name[code_point]};")
            except KeyError:
                # And fall back to a numeric entity
                new_text_list.append(f"&#{code_point};")
    return "".join(new_text_list)


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


def format_duration(duration):
    attrs = ["years", "months", "days", "hours", "minutes", "seconds"]
    delta = relativedelta(seconds=duration)
    return ", ".join(
        [
            "%d %s"
            % (
                getattr(delta, attr),
                attr if getattr(delta, attr) > 1 else attr[:-1],
            )
            for attr in attrs
            if getattr(delta, attr)
        ]
    )


def get_links(html_file):
    soup = BeautifulSoup(open(html_file), "html.parser")
    link = soup.find("link", rel="canonical")
    base_url = None
    if link:
        url = urlparse(link["href"])
        base_url = f"{url.scheme}://{url.netloc}"

    links = set()
    for a in soup.find_all("a"):
        link = a["href"]
        if link.startswith("#"):
            continue

        no_host = link.startswith("/")
        if no_host and base_url:
            link = f"{base_url}{link}"
        elif no_host:
            continue

        links.add(link)

    return list(links)


def get_methods(obj, *includes):
    methods = {}

    for attr_name in sorted(dir(obj)):
        attr_val = getattr(obj, attr_name)

        if attr_name not in includes:
            if attr_name.startswith("_") or not callable(attr_val):
                continue
            if len(inspect.signature(attr_val).parameters) > 0:
                continue

        methods[attr_name] = attr_val

    return methods


def get_text_long(self, expr, **kwargs):
    return util.xpath(
        self.root,
        expr,
        all_text=True,
        join_text=True,
        sep=" ",
        join_sep=" ",
        ignore_space=True,
        **kwargs,
    )


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


def has_newline(text_list):
    return any("\n" in text for text in text_list)


def is_dlts_handle(url_str):
    url = urlparse(url_str)
    return url.netloc == "hdl.handle.net" and re.search(
        r"^/2333.1/[a-z0-9]+$", url.path
    )


def is_str(lst):
    return (
        len(lst) == 1
        and type(lst[0]) is str
        and len(lst[0]) > 240
        # and "http" not in lst[0]
    )


def is_url(url):
    return urlparse(url).scheme in ["http", "https"] and not url.endswith("\n")


def parse_level(c):
    level, recursion = c["class"].split()
    level = level.split("-", maxsplit=1)[1]
    recursion = int(recursion[-1])
    return (level, recursion)


def pretty_format(mydict):
    return json.dumps(mydict, indent=2)


def quote(val):
    if type(val) == str:
        return f"'{val}'"
    else:
        return str(val)


# https://stackoverflow.com/questions/18159221/remove-namespace-and-prefix-from-xml-in-python-using-lxml
def remove_namespace(doc, namespace):
    """Remove namespace in the passed document in place."""
    ns = "{%s}" % namespace
    nsl = len(ns)
    for elem in doc.iter():
        local_elem_name = ET.QName(elem).localname
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]
        for attr_name in elem.attrib:
            local_attr_name = ET.QName(attr_name).localname
            if attr_name.startswith(ns):
                elem.attrib[attr_name[nsl:]] = elem.attrib.pop(attr_name)


def resolve_handle(url):
    response = requests.get(url, allow_redirects=False)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.a["href"]


def sort_dict(mydict):
    return dict(sorted(mydict.items(), key=lambda item: item[1]))


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


def strings(tag):
    text = ""
    for string in tag.strings:
        text += string
    return text


def strip_date(title):
    title_list = title.rsplit(":", 1)
    if len(title_list) == 1:
        return title
    try:
        date = parse(title_list[1])
        return title_list[0]
    except ParserError as e:
        return title


def tag_text(tag):
    return "".join(tag.itertext())


def xpath(
    root,
    expr,
    all_text=False,
    join_text=False,
    join_uniq=True,
    sep="",
    join_sep="",
    ignore_space=False,
):
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
        elif all_text:
            strings = []
            for string in node.itertext():
                if ignore_space:
                    if string.isspace():
                        continue
                    else:
                        string = string.strip()
                strings.append(string)
            text = clean_text(sep.join(strings)) if strings else None
        else:
            text = clean_text(node.text) if node.text else None

        if not text:
            continue

        result.add(node.tag, text, node.sourceline)

    if join_text and result:
        result = result.join(sep=join_sep, uniq=join_uniq)

    return result if result else None
