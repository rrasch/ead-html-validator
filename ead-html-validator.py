#!/usr/bin/env -S python3 -u


# from fuzzywuzzy import fuzz
# from fuzzywuzzy import process
from importlib import import_module
from lxml import etree as ET
from pathlib import Path
from pprint import pprint
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

red = lambda text: colored(255, 0, 0, text)
green = lambda text: colored(0, 255, 0, text)
blue = lambda text: colored(0, 0, 255, text)


def diff(obj1, obj2):
    if type(obj1) is str:
        return diff_str(obj1, obj2)
    else:
        return diff_list(obj1, obj2)


def diff_str(str1, str2):
    result = ""
    codes = difflib.SequenceMatcher(a=str1, b=str2).get_opcodes()
    for code in codes:
        if code[0] == "equal":
            result += str1[code[1]:code[2]]
        elif code[0] == "delete":
            result += red(str1[code[1]:code[2]])
        elif code[0] == "insert":
            result += green(str2[code[3]:code[4]])
        elif code[0] == "replace":
            result += (red(str1[code[1]:code[2]]) + green(str2[code[3]:code[4]]))
    return result


def diff_list(list1, list2):
    result = []
    codes = difflib.SequenceMatcher(a=list1, b=list2).get_opcodes()
    for code in codes:
        if code[0] == "equal":
            result.extend(list1[code[1]:code[2]])
        elif code[0] == "delete":
            result.extend( map(red, list1[code[1]:code[2]] ) )
        elif code[0] == "insert":
            result.extend( map(green, list2[code[3]:code[4]]) )
        elif code[0] == "replace":
            result.extend( map(red, list1[code[1]:code[2]]))
            result.extend( map(green, list2[code[3]:code[4]]))
    return result


def compare(val1, val2):
    val1 = val1 or ""
    val2 = val2 or ""
    if type(val1) is not list:
        val1 = [val1]
    if type(val2) is not list:
        val2 = [val2]
    return val1 == val2


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
                    print(ret.stderr)


def validate_xml(xml_file):
    xmllint = shutil.which("xmllint")
    if xmllint:
        return util.do_cmd(
            [xmllint, "--noout", "--schema", "ead.xsd", xml_file]
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
            print(sys.exc_info())
        else:
            globals()[libname] = lib

def validate_component(c, dirpath, errors):
    print("----")
    print(c.id())
    print(c.level())
    print(c.title())
    print()

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
        logging.debug(f"calling Component.{method_name}()")
        comp_retval = comp_method()
        logging.debug(f"retval={comp_retval}")

        match = re.search(r"^(sub_components|unitid)$", method_name)
        if match:
            print(f"Skipping {method_name}...")
            continue

        chtml_method = getattr(chtml, method_name)
        logging.debug(f"calling CompHTML.{method_name}()")
        chtml_retval = chtml_method()
        logging.debug(f"retval={chtml_retval}")

        passed_check = compare(comp_retval, chtml_retval)
        if not passed_check:
            errors.append(
                f"{method_name} compenent({c.id()}) - '{comp_retval}' !="
                f" '{chtml_retval}'"
            )

    for sub_c in c.sub_components():
        # print(sub_c)
        # print(sub_c.id())
        # print(sub_c.level())
        validate_component(sub_c, new_dirpath, errors)


def main():
    script_name = Path(__file__).stem

    logging.basicConfig(
        format=f"%(asctime)s - {script_name} - %(levelname)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )

    parser = argparse.ArgumentParser(description="Validate.")
    parser.add_argument("ead_file", metavar="EAD_FILE", help="ead file")
    parser.add_argument("html_dir", metavar="HTML_DIR", help="html directory")
    parser.add_argument(
        "-d", "--debug", help="Enable debugging messages", action="store_true"
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.debug("ead file: %s", args.ead_file)
    logging.debug("html dir: %s", args.html_dir)

    validate_xml(args.ead_file)
    validate_html(args.html_dir)

    my_ead = ead.Ead(args.ead_file)

    html_file = os.path.join(args.html_dir, "index.html")
    ehtml = eadhtml.EADHTML(html_file)

    rqm_html_file = os.path.join(args.html_dir, "requestmaterials", "index.html")
    rqm = RequestMaterials(rqm_html_file)
    pprint(rqm.find_links())

    load_fuzzywuzzy()

    errors = []

    for method_name, ead_method in util.get_methods(my_ead).items():
        ehtml_method = getattr(ehtml, method_name)

        logging.debug(f"calling EAD.{method_name}()")
        ead_retval = ead_method()
        logging.debug(f"retval={ead_retval}")

        match = re.search(r"^(dao|component|altformavail)$", method_name)
        if match:
            print(f"Skipping {method_name}...")
            continue

        logging.debug(f"calling EADHTML.{method_name}()")
        ehtml_retval = ehtml_method()
        logging.debug(f"retval={ehtml_retval}")

        passed_check = compare(ead_retval, ehtml_retval)
        if not passed_check:
            errors.append(f"{method_name} - {ead_retval} != {ehtml_retval}")
            print(diff(ead_retval, ehtml_retval))
            exit(1)

        if ehtml_retval is None:
            exit(1)

    for c in my_ead.component():
        validate_component(c, args.html_dir, errors)

    for error in errors:
        print(f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
