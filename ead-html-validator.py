#!/usr/bin/env -S python3 -u


from anytree import Node, RenderTree
from collections import defaultdict
from component import Component
from importlib import import_module
from lxml import etree as ET
from pathlib import Path
from pprint import pprint, pformat
from requestmaterials import RequestMaterials
from resultset import ResultSet
from subprocess import PIPE
# from thefuzz import fuzz
# from thefuzz import process
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
import tomli
import traceback
import shutil
import sys
import util


print = functools.partial(print, flush=True)

# def colorize(r, g, b, text):
#     return f"\033[38;2;{r};{g};{b}m{text}\033[0m"
#
# red = lambda text: colored(255, 0, 0, text)
# green = lambda text: colored(0, 255, 0, text)
# blue = lambda text: colored(0, 0, 255, text)

def colorize(color_code, text):
    return f"\033[{color_code}m{text}\033[0m" if COLORS_ENABLED else text

red   = lambda text: colorize(31, text)
green = lambda text: colorize(32, text)
blue  = lambda text: colorize(34, text)
bold  = lambda text: colorize(1,  text)

diff_color = {
    "+": green,
    "-": red,
    "^": blue,
}

pass_color = {
    True: green,
    False: red,
}

def stringify_list(mylist):
    return [
        util.pretty_format(elem) if isinstance(elem, dict) else elem
        for elem in mylist
    ]

def diff(obj1, obj2, diff_cfg):
    list1 = stringify_list(create_list(obj1))
    list2 = stringify_list(create_list(obj2))
    if diff_cfg["type"].startswith("unified"):
        text = ""
        for uni_diff in difflib.unified_diff(list1, list2):
            if diff_cfg["type"].endswith("color") and uni_diff[0] in diff_color:
                text += diff_color[uni_diff[0]](uni_diff) + "\n"
            else:
                text += uni_diff + "\n"
    elif diff_cfg["type"] == "color":
        if util.is_str(list1) and util.is_str(list2):
            text = color_diff_str(list1[0], list2[0])
        else:
            text = color_diff_list(list1, list2)
    else:
        text = simple_diff(obj1, obj2, diff_cfg)
    return diff_cfg["sep"] + "\n" + text.strip() + "\n" + diff_cfg["sep"]

def simple_diff(obj1, obj2, diff_cfg):
    max_len = diff_cfg["term_width"]
    str1 = str(obj1)
    str2 = str(obj2)
    sep = "\n" if len(str1) + len(str2) + 3 > 80 else " "
    # return f"{str1[:max_len]}{sep}!={sep}{str2[:max_len]}"
    return f"{str1}{sep}!={sep}{str2}"

def color_diff_str(str1, str2):
    logging.debug(f"color_diff({str1}, {str2})")
    result = ""
    codes = difflib.SequenceMatcher(a=str1, b=str2).get_opcodes()
    for code in codes:
        if code[0] == "equal":
            result += str1[code[1] : code[2]]
        elif code[0] == "delete":
            result += red(str1[code[1] : code[2]])
        elif code[0] == "insert":
            result += green(str2[code[3] : code[4]])
        elif code[0] == "replace":
            result += red(str1[code[1] : code[2]]) + green(
                str2[code[3] : code[4]]
            )
    return result


def quote(val):
    return f"'{val}'"

def color_diff_list(list1, list2):
    result = []

    try:
        codes = difflib.SequenceMatcher(a=list1, b=list2).get_opcodes()
    except TypeError as e:
        logging.error(f"list1:\n{util.pretty_print(list1)}")
        logging.error(f"list2:\n{util.pretty_print(list2)}")
        raise e

    for code in codes:
        if code[0] == "equal":
            result.extend(list1[code[1]:code[2]])
        elif code[0] == "delete":
            result.extend(map(red, list1[code[1]:code[2]]))
        elif code[0] == "insert":
            result.extend(map(green, list2[code[3]:code[4]]))
        elif code[0] == "replace":
            result.extend(map(red, list1[code[1]:code[2]]))
            result.extend(map(green, list2[code[3]:code[4]]))
    return  "[" + ", ".join(map(quote, result)) + "]"

def comparable_val(val):
    val = val or ""
    if type(val) is not list:
        val = [val]
    try:
        if type(val[0]) is str:
            val = sorted(val)
        elif type(val[0]) is dict:
            val = sorted(val, key=lambda x: next(iter(x)))
        else:
            val = val.sort()
    except TypeError as e:
        logging.error(f"val1: {pformat(val)}")
        raise e
    return val

def compare(val1, val2):
    return comparable_val(val1) ==  comparable_val(val2)

def create_list(obj):
    if type(obj) is not list:
        return [obj]
    else:
        return obj

def validate_html(html_dir, args):
    html_files = []
    for root, dirs, files in os.walk(html_dir):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))

    if args.broken_links:
        links = defaultdict(set)
        for file in html_files:
            for url in util.get_links(file):
                links[url].add(file)
        urls = sorted(list(links.keys()))
        logging.trace(f"Testing the following links: {pformat(urls)}")
        broken_links = util.find_broken_links(urls)
        if broken_links:
            logging.warn("The following links are broken {broken_links}")

    path_tidy = shutil.which("tidy")
    if (args.tidy or args.indent) and path_tidy:
        for file in html_files:
            ret = util.do_cmd(
                [path_tidy, file],
                allowed_returncodes=[1, 2],
                stdout=PIPE,
                stderr=PIPE,
            )
            if ret:
                logging.debug(ret.stderr)
                indented_file = os.path.splitext(file)[0] + "-tidy.html"
                if args.indent and not os.path.exists(indented_file):
                    with open(indented_file, "w") as wfh:
                        wfh.write(ret.stdout)


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

def load_thefuzz():
    for libname in ["fuzz", "process"]:
        try:
            lib = import_module(f"thefuzz.{libname}")
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

def format_vals(vals):
    if type(vals) is dict:
        return "\n".join([f"Line {k}: '{v}'" for k, v in vals.items()])
    else:
        # return repr(vals)
        return str(vals)

def passed_str(passed):
    status = "PASS" if passed else "FAIL"
    status = pass_color[passed](status)
    return status

def check_retval(retval, name):
    if retval is not None and not isinstance(retval, ResultSet):
        raise ValueError(
            f"Expected ResultSet for {name}, got {retval} instead."
        )

def validate_component(c, dirpath, errors, diff_cfg, excludes):
    logging.debug("----")
    logging.debug(c.id)
    logging.debug(c.level)
    logging.debug(c.title())
    logging.debug("\n")

    new_dirpath = dirpath

    if c.level == "series":
        new_dirpath = os.path.join(new_dirpath, "contents", c.id)

    html_file = os.path.join(new_dirpath, "index.html")
    logging.debug(f"HTML file: {html_file}")
    ehtml = eadhtml.EADHTML(html_file)

    try:
        chtml = ehtml.find_component(c.id)
    except eadhtml.ComponentNotFoundError as e:
        # errors.append(traceback.format_exc())
        errors.append(repr(e))
        return

    # logging.debug(chtml)
    logging.debug(f"chtml id:     {chtml.id}")
    logging.debug(f"chtml level:  {chtml.level}")
    logging.debug(f"chtml title:  {chtml.title()}")
    logging.debug(f"chtml extent: {chtml.extent()}")

    logging.debug(f"component tag: {c.c.tag}")

    logging.info(f"Performing checks for container {c.id}")

    # XXX: Should this be replaced by constants?
    for method_name, comp_method in util.get_methods(c).items():
        match = re.search(r"^(sub_components)$", method_name)
        if match:
            logging.debug(f"Skipping {method_name}...")
            continue

        if method_name in excludes["container"]["checks"]:
            logging.debug(f"Skipping {method_name}...")
            continue

        logging.debug(f"calling Component.{method_name}()")
        comp_retval = comp_method()
        logging.debug(f"retval={comp_retval}")
        check_retval(comp_retval, method_name)

        if type(comp_retval) in [dict, ResultSet]:
            comp_values = list(comp_retval.values())
        else:
            comp_values = comp_retval

        logging.debug(f"calling CompHTML.{method_name}()")
        chtml_method = getattr(chtml, method_name)
        chtml_retval = chtml_method()
        logging.debug(f"retval={chtml_retval}")
        check_retval(chtml_retval, method_name)

        if type(chtml_retval) in [dict, ResultSet]:
            chtml_values = list(chtml_retval.values())
        else:
            chtml_values = chtml_retval

        missing_err_template = (
            "Value not set for field '{}' in container"
            " '{}' inside {} file '{}' \nbut found"
            " values:\n{}\ninside '{}'"
        )

        passed_check = False
        if comp_retval is not None and chtml_retval is None:
            errors.append(
                missing_err_template.format(
                    bold(method_name),
                    c.id,
                    "html",
                    html_file,
                    format_vals(comp_retval),
                    c.ead_file,
                )
            )
        elif comp_retval is None and chtml_retval is not None:
            errors.append(
                missing_err_template.format(
                    method_name,
                    c.id,
                    "ead xml",
                    c.ead_file,
                    format_vals(chtml_retval),
                    html_file,
                )
            )
        else:
            passed_check = compare(comp_values, chtml_values)
            if not passed_check:
                errors.append(
                    f"field '{method_name}' differs for c"
                    f" id='{c.id}'\nDIFF:\n"
                    + diff(comp_values, chtml_values, diff_cfg)
                )

        logging.info(f"{c.id} {method_name}: [{passed_str(passed_check)}]")

    ead_subc_list = c.sub_components()
    ead_cids = [(subc.id, subc.level) for subc in ead_subc_list]
    html_cids = chtml.component_id_level()

    logging.debug(f"EAD CIDS {ead_cids}")
    logging.debug(f"HTML CIDS {html_cids}")

    if ead_cids != html_cids:
        errors.append(
            f"Nesting level error at level ({c.id},"
            f" {c.level}):\nExpected:\n{pformat(ead_cids)}\nbut"
            f" got:\n{pformat(html_cids)}"
        )

    for subc in c.sub_components():
        # logging.debug(subc)
        # logging.debug(subc.id)
        # logging.debug(subc.level)
        validate_component(subc, new_dirpath, errors, diff_cfg, excludes)


def build_level_tree(ead_elem, parent):
    if isinstance(ead_elem, Component):
        comps = ead_elem.sub_components()
    else:
        comps = ead_elem.component()

    for c in comps:
        child = Node((c.id, c.level), parent=parent)
        build_level_tree(c, child)

def render_level_tree(ead_elem, root_name):
    root = Node(root_name)
    build_level_tree(ead_elem, root)
    # iterator = iter(RenderTree(root))
    # pre, fill, node = next(iterator)
    return [f"{pre}{node.name}\n" for pre, fill, node in RenderTree(root)]

def read_excludes():
    with open("excludes.toml", "rb") as f:
        data = tomli.load(f)
    return data

def main():

    if not sys.version_info >= (3, 7):
        print("Python 3.7 or higher is required.")
        exit(1)

    script_name = Path(__file__).stem

    parser = argparse.ArgumentParser(
        description="Validate finding aids html against ead xml file.")
    parser.add_argument("ead_file", metavar="EAD_FILE", help="ead file")
    parser.add_argument("html_dir", metavar="HTML_DIR", help="html directory")
    parser.add_argument("--diff-type", default="simple",
        choices=["color", "unified", "unified-color", "simple"],
        help="diff type (default: %(default)s)"
    )
    parser.add_argument("--verbose", "-v", action="count", default=0,
        help=("Verbose mode. Multiple -v options increase the verbosity."
            " The maximum is 3."))
    parser.add_argument("--log-format", "-l",
        default=f"%(asctime)s - {script_name} - %(levelname)s - %(message)s",
        help="format for logging messages (default: %(default)s)")
    parser.add_argument("--tidy", "-t", action="store_true",
        help="Run HTML Tidy to test correctness of html")
    parser.add_argument("--indent", "-i", action="store_true",
        help="Indent HTML files using tidy.")
    parser.add_argument("--broken-links", "-b", action="store_true",
        help="Find broken urls")
    parser.add_argument("--color", "-c", action="store_true",
        help="Enable color output")
    args = parser.parse_args()

    global COLORS_ENABLED
    COLORS_ENABLED = args.color or "color" in args.diff_type

    logging.basicConfig(format=args.log_format, datefmt="%m/%d/%Y %I:%M:%S %p")

    util.addLoggingLevel("TRACE", logging.DEBUG - 5)

    if args.verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif args.verbose == 2:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose == 3:
        logging.getLogger().setLevel(logging.TRACE)
    elif args.verbose:
        print("You can only specify -v a maximum of 3 times.", file=sys.stderr)
        parser.print_help(sys.stderr)
        exit(1)

    excludes = read_excludes()
    logging.debug(excludes)

    ead_file = os.path.abspath(args.ead_file)
    html_dir = os.path.abspath(args.html_dir)

    logging.debug("ead file: %s", ead_file)
    logging.debug("html dir: %s", html_dir)

    validate_xml(ead_file)
    validate_html(html_dir, args)

    my_ead = ead.Ead(ead_file)

    html_file = os.path.join(html_dir, "index.html")
    ehtml = eadhtml.EADHTML(html_file)

    rqm_html_file = os.path.join(html_dir, "requestmaterials", "index.html")
    rqm = RequestMaterials(rqm_html_file)
    logging.debug(pformat(rqm.find_links()))

    all_html_file = os.path.join(html_dir, "all", "index.html")
    all_ehtml = eadhtml.EADHTML(all_html_file)
    names = all_ehtml.names()

    load_thefuzz()

    errors = []

    term_width = get_term_width()

    diff_cfg = {
        "type": args.diff_type,
        "term_width": term_width,
        "sep": "-" * term_width,
    }

    logging.info("Performing top level checks.")

    for method_name, ead_method in util.get_methods(my_ead).items():
        match = re.search(r"^(component)$", method_name)
        if match:
            logging.debug(f"Skipping {method_name}...")
            continue

        if method_name in excludes["top"]["checks"]:
            logging.debug(f"Skipping {method_name}...")
            continue

        logging.debug(f"calling EAD.{method_name}()")
        ead_retval = ead_method()
        logging.debug(f"retval={ead_retval}")
        check_retval(ead_retval, method_name)

        if type(ead_retval) in [ResultSet]:
            ead_values = ead_retval.values()
        else:
            ead_values = ead_retval

        logging.debug(f"calling EADHTML.{method_name}()")
        ehtml_method = getattr(ehtml, method_name)
        ehtml_retval = ehtml_method() if method_name != "names" else names
        logging.debug(f"retval={ehtml_retval}")
        check_retval(ehtml_retval, method_name)

        if type(ehtml_retval) in [ResultSet]:
            ehtml_values = ehtml_retval.values()
        else:
            ehtml_values = ehtml_retval

        passed_check = compare(ead_values, ehtml_values)
        logging.info(f"{method_name}: [{passed_str(passed_check)}]")
        if not passed_check:
            errors.append(
                f"ead field '{method_name}' differs'\nDIFF:\n"
                + diff(ead_values, ehtml_values, diff_cfg)
            )

        if ehtml_retval is None:
            print("Missing value")

    ead_comps = my_ead.component()
    ead_cids = [(c.id, c.level) for c in ead_comps]
    html_cids = all_ehtml.component_id_level()

    logging.info("Performing nesting level check.")

    ead_tree = render_level_tree(my_ead, ead_file)
    ead_tree_str = "".join(ead_tree)
    logging.debug(f"EAD Nesting Level Tree\n{ead_tree_str}")

    html_tree = render_level_tree(all_ehtml, all_html_file)
    html_tree_str = "".join(html_tree)
    logging.debug(f"HTML Nesting Level Tree\n{html_tree_str}")

    passed_check =  ead_tree[1:] == html_tree[1:]
    logging.info(f"nesting levels: [{passed_str(passed_check)}]")
    if not passed_check:
        errors.append("Nesting error" + diff(ead_tree_str, html_tree_str, diff_cfg))

    logging.debug(f"EAD CIDS {ead_cids}")
    logging.debug(f"HTML CIDS {html_cids}")

    if ead_cids != html_cids:
        errors.append(
            "Nesting level error at top"
            f" level:\nExpected:\n{pformat(ead_cids)}\nbut"
            f" got:\n{pformat(html_cids)}"
        )

    for c in ead_comps:
        validate_component(c, html_dir, errors, diff_cfg, excludes)

    for error in errors:
        print(f"ERROR: {error}\n")

    logging.info("Validation complete.")
    exit(len(errors))

if __name__ == "__main__":
    main()
