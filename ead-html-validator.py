#!/usr/bin/env -S python3 -u


# from fuzzywuzzy import fuzz
# from fuzzywuzzy import process
from importlib import import_module
from lxml import etree as ET
from pathlib import Path
from pprint import pprint, pformat
from requestmaterials import RequestMaterials
from subprocess import PIPE
import argparse
import constants
import difflib
import ead
import eadhtml
import functools
import inspect
import logging
import os.path
import re
import traceback
import shutil
import sys
import util


print = functools.partial(print, flush=True)

def colored(r, g, b, text):
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

# red = lambda text: colored(255, 0, 0, text)
# green = lambda text: colored(0, 255, 0, text)
# blue = lambda text: colored(0, 0, 255, text)

red = lambda text: f"\033[31m{text}\033[0m"
green = lambda text: f"\033[32m{text}\033[0m"
blue = lambda text: f"\033[34m{text}\033[0m"
foo = lambda text: text

diff_color = {
    "+": green,
    "-": red,
    "^": blue,
}

def diff(obj1, obj2, diff_cfg):
    list1 = create_list(obj1)
    list2 = create_list(obj2)
    if diff_cfg['type'].startswith("unified"):
        print("type obj1", type(obj1))
        text = ""
        for uni_diff in difflib.unified_diff(list1, list2):
            if diff_type.endswith("color") and uni_diff[0] in diff_color:
                text += diff_color[uni_diff[0]](uni_diff) + "\n"
            else:
                text += uni_diff + "\n"
        text = "\n" + text.strip()
    elif diff_cfg["type"] == "color":
        text = color_diff_list(list1, list2)
    else:
        text = simple_diff(obj1, obj2, diff_cfg)
    return diff_cfg["sep"] + "\n" + text + diff_cfg["sep"] + "\n"

def simple_diff(obj1, obj2, diff_cfg):
    max_len = diff_cfg["term_width"]
    return f"{repr(obj1)[:max_len]}\n!=\n{repr(obj2)[:max_len]}\n"

def color_diff_str(str1, str2):
    logging.debug(f"color_diff({str1}, {str2})")
    result = ""
    codes = difflib.SequenceMatcher(a=str1, b=str2).get_opcodes()
    for code in codes:
        if code[0] == "equal":
            result += foo(str1[code[1]:code[2]])
        elif code[0] == "delete":
            result += red(str1[code[1]:code[2]])
        elif code[0] == "insert":
            result += green(str2[code[3]:code[4]])
        elif code[0] == "replace":
            result += (red(str1[code[1]:code[2]]) + green(str2[code[3]:code[4]]))
    return result


def quote(val):
    return f"'{val}'"

def color_diff_list(list1, list2):
    result = []
    codes = difflib.SequenceMatcher(a=list1, b=list2).get_opcodes()
    for code in codes:
        if code[0] == "equal":
            # result.extend(list1[code[1]:code[2]])
            result.extend(map(foo, list1[code[1]:code[2]]))
        elif code[0] == "delete":
            result.extend(map(red, list1[code[1]:code[2]]))
        elif code[0] == "insert":
            result.extend(map(green, list2[code[3]:code[4]]))
        elif code[0] == "replace":
            result.extend(map(red, list1[code[1]:code[2]]))
            result.extend(map(green, list2[code[3]:code[4]]))
    return  "[" + ", ".join(map(quote, result)) + "]"


def compare(val1, val2):
    val1 = val1 or ""
    val2 = val2 or ""
    if type(val1) is not list:
        val1 = [val1]
    if type(val2) is not list:
        val2 = [val2]
    return sorted(val1) == sorted(val2)

def create_list(obj):
    if type(obj) is str:
        return [obj]
    else:
        return obj

def validate_html(html_dir):
    tidy = shutil.which("tidy")
    if not tidy:
        return None

    for root, dirs, files in os.walk(html_dir):
        for file in files:
            if file.endswith(".html"):
                ret = util.do_cmd(
                    [tidy, os.path.join(root, file)],
                    allowed_returncodes=[1, 2],
                    stdout=PIPE,
                    stderr=PIPE,
                )
                if ret:
                    logging.debug(ret.stderr)


def validate_xml(xml_file):
    xmllint = shutil.which("xmllint")
    if xmllint:
        return util.do_cmd(
            [xmllint, "--noout", "--schema", "ead.xsd", xml_file],
                    stdout=PIPE,
                    stderr=PIPE,
        )
    else:
        try:
            schema = ET.XMLSchema(ET.parse("ead.xsd"))
            result = schema.validate(ET.parse(xml_file))
        except Exception as e:
            raise e

def load_fuzzywuzzy():
    for libname in ["fuzz", "process"]:
        try:
            lib = import_module(f"fuzzywuzzy.{libname}")
        except:
            logging.debug(sys.exc_info())
        else:
            globals()[libname] = lib

def get_term_width():
    try:
        term_size = os.get_terminal_size()
        term_width = term_size.columns
    except:
        term_width = 80
    return term_width

def validate_component(c, dirpath, errors, diff_cfg):
    logging.debug("----")
    logging.debug(c.id())
    logging.debug(c.level())
    logging.debug(c.title())
    logging.debug("\n")

    new_dirpath = dirpath

    if c.level() == "series":
        new_dirpath = os.path.join(new_dirpath, "contents", c.id())

    html_file = os.path.join(new_dirpath, "index.html")
    logging.debug(f"HTML file: {html_file}")
    ehtml = eadhtml.EADHTML(html_file)

    try:
        chtml = ehtml.find_component(c.id())
    except eadhtml.ComponentNotFoundError as e:
        # errors.append(traceback.format_exc())
        errors.append(repr(e))
        return

    # logging.debug(chtml)
    logging.debug(f"chtml id:     {chtml.id()}")
    logging.debug(f"chtml level:  {chtml.level()}")
    logging.debug(f"chtml title:  {chtml.title()}")
    logging.debug(f"chtml extent: {chtml.extent()}")

    logging.debug(f"component tag: {c.c.tag}")

    # XXX: Should this be replaced by constants?
    for method_name, comp_method in util.get_methods(c).items():
        match = re.search(r"^(sub_components|unitid)$", method_name)
        if match:
            logging.debug(f"Skipping {method_name}...")
            continue

        logging.debug(f"calling Component.{method_name}()")
        comp_retval = comp_method()
        logging.debug(f"retval={comp_retval}")

        logging.debug(f"calling CompHTML.{method_name}()")
        chtml_method = getattr(chtml, method_name)
        chtml_retval = chtml_method()
        logging.debug(f"retval={chtml_retval}")

        if comp_retval is not None and chtml_retval is None:
            errors.append(
                f"Can't find the value of field '{method_name}' in c"
                f" id='{c.id()}' within html file '{html_file}'"
                f" \n'{comp_retval}'"
            )
        elif comp_retval is None and chtml_retval is not None:
            errors.append(
                f"Can't find the value of field '{method_name}' in c"
                f" id='{c.id()}' within ead file '{c.ead_file}'"
            )
        else:
            passed_check = compare(comp_retval, chtml_retval)
            if not passed_check:
                errors.append(f"field '{method_name}' differs for c '{c.id()}'\n\nDIFF: " + diff(comp_retval, chtml_retval, diff_cfg) + "\n")

    for sub_c in c.sub_components():
        # logging.debug(sub_c)
        # logging.debug(sub_c.id())
        # logging.debug(sub_c.level())
        validate_component(sub_c, new_dirpath, errors, diff_cfg)


def main():

    if not sys.version_info >= (3, 7):
        print("Python 3.6 or higher is required.")
        sys.exit(1)

    script_name = Path(__file__).stem

    logging.basicConfig(
        format=f"%(asctime)s - {script_name} - %(levelname)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )

    parser = argparse.ArgumentParser(description="Validate.")
    parser.add_argument("ead_file", metavar="EAD_FILE", help="ead file")
    parser.add_argument("html_dir", metavar="HTML_DIR", help="html directory")
    parser.add_argument("--diff-type", default="unified",
        choices=["color", "unified", "unified-color", "simple"],
        help="diff type (color, unified, or simple)"
    )
    parser.add_argument(
        "-d", "--debug", help="Enable debugging messages", action="store_true"
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    ead_file = os.path.abspath(args.ead_file)
    html_dir = os.path.abspath(args.html_dir)

    logging.debug("ead file: %s", ead_file)
    logging.debug("html dir: %s", html_dir)

    validate_xml(ead_file)
    validate_html(html_dir)

    my_ead = ead.Ead(ead_file)

    html_file = os.path.join(html_dir, "index.html")
    ehtml = eadhtml.EADHTML(html_file)

    rqm_html_file = os.path.join(html_dir, "requestmaterials", "index.html")
    rqm = RequestMaterials(rqm_html_file)
    logging.debug(pformat(rqm.find_links()))

    load_fuzzywuzzy()

    errors = []

    term_width = get_term_width()

    diff_cfg = {
        "type": args.diff_type,
        "term_width": term_width,
        "sep": "-" * term_width,
    }

    for method_name, ead_method in util.get_methods(my_ead).items():
        match = re.search(r"^(dao|component|altformavail)$", method_name)
        if match:
            logging.debug(f"Skipping {method_name}...")
            continue

        logging.debug(f"calling EAD.{method_name}()")
        ead_retval = ead_method()
        logging.debug(f"retval={ead_retval}")

        logging.debug(f"calling EADHTML.{method_name}()")
        ehtml_method = getattr(ehtml, method_name)
        ehtml_retval = ehtml_method()
        logging.debug(f"retval={ehtml_retval}")


        passed_check = compare(ead_retval, ehtml_retval)
        if not passed_check:
            errors.append(f"ead field '{method_name}' differs'\n\nDIFF\n: " + diff(ead_retval, ehtml_retval, diff_cfg) + "\n")

        if ehtml_retval is None:
            exit(1)

    for c in my_ead.component():
        validate_component(c, html_dir, errors, diff_cfg)

    with open("output.log", "w") as f:
        for error in errors:
            print(f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
