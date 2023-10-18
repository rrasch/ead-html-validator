#!/usr/bin/env -S python3

from anytree import Node, RenderTree
from cachetools import LRUCache
from collections import defaultdict
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    as_completed,
)
from ead_html_validator import Component
from ead_html_validator import EADHTML
from ead_html_validator import Ead
from ead_html_validator import Errors
from ead_html_validator import RequestMaterials
from ead_html_validator import ResultSet
from ead_html_validator import util
from importlib import import_module
from lxml import etree as ET
from multiprocessing import Manager, get_context
from pathlib import Path
from pprint import pprint, pformat
from subprocess import PIPE
from tqdm import tqdm
from typing import List
import argparse
import difflib
import functools
import inflect
import inspect
import logging
import os.path
import pkg_resources
import re
import shutil
import sys
import textwrap
import threading
import time
import tomli
import traceback


print = functools.partial(print, flush=True)


class EHTMLCache(LRUCache):
    def popitem(self):
        html_file, ehtml = super().popitem()
        logging.debug(f"HTML file '{html_file}' removed from EADHTML cache")
        return html_file, ehtml


def colorize(text, *color_codes) -> str:
    color_seq = ";".join(map(str, color_codes))
    return f"\033[{color_seq}m{text}\033[0m" if colors_enabled else text


def colorize_space(text, color_text, color_space) -> str:
    new_text = ""
    for s in re.split("(\s+)", text):
        if s.isspace():
            new_text += color_space(s)
        elif s:
            new_text += color_text(s)
    return new_text


red           = lambda text: colorize(text, 31)
red_gray      = lambda text: colorize(text, 31, 47)
red_ltred     = lambda text: colorize(text, 31, 101)
green         = lambda text: colorize(text, 32)
green_gray    = lambda text: colorize(text, 32, 47)
green_ltgreen = lambda text: colorize(text, 32, 102)
blue          = lambda text: colorize(text, 34)
bold          = lambda text: colorize(text, 1)

delete_color = lambda text: colorize_space(text, red, red_ltred)
insert_color = lambda text: colorize_space(text, green, green_ltgreen)


diff_color = {
    "+": green,
    "-": red,
    "^": blue,
}

pass_color = {
    True: green,
    False: red,
}


def stringify_list(mylist) -> List[str]:
    return [
        util.pretty_format(elem) if isinstance(elem, dict) else elem
        for elem in mylist
    ]


def diff(data1, data2, diff_cfg) -> str:
    if type(data1) != type(data2):
        raise TypeError("Diff args must be same type.")

    types = [list, ResultSet]
    if not any([isinstance(data1, t) for t in types]):
        raise TypeError(f"Diff args must be list be {types}")

    list1 = None
    list2 = None

    if isinstance(data1, list):
        list1 = data1
        list2 = data2

    if diff_cfg["type"] == "simple":
        if list1 is None:
            list1 = data1.values()
            list2 = data2.values()
        text = simple_diff(list1, list2, diff_cfg)
    else:
        if list1 is None:
            list1 = data1.string_values()
            list2 = data2.string_values()
        if diff_cfg["type"].startswith("unified"):
            text = ""
            for uni_diff in difflib.unified_diff(list1, list2):
                if (
                    diff_cfg["type"].endswith("color")
                    and uni_diff[0] in diff_color
                ):
                    text += diff_color[uni_diff[0]](uni_diff) + "\n"
                else:
                    text += uni_diff + "\n"
        else:
            if util.is_str(list1) and util.is_str(list2):
                text = color_diff_str(list1[0], list2[0])
            else:
                text = color_diff_list(list1, list2)
    return diff_cfg["sep"] + "\n" + text.strip() + "\n" + diff_cfg["sep"]


def indent_and_join(text_list) -> str:
    return (
        "[\n"
        + ",\n".join([textwrap.indent(text, "  ") for text in text_list])
        + "\n]"
    )


def simple_diff(list1, list2, diff_cfg) -> str:
    max_len = diff_cfg["term_width"]
    str1 = str(list1)
    str2 = str(list2)
    if (
        "\n" not in str1
        and "\n" not in str2
        and len(str1) + len(str2) + 3 <= max_len
    ):
        sep = " "
    else:
        str1 = pformat(list1)
        str2 = pformat(list2)
        sep = "\n"
    diff_text = f"{str1}{sep}!={sep}{str2}"
    return diff_text


def color_diff_str(str1, str2) -> str:
    # logging.debug(f"color_diff({str1}, {str2})")
    result = ""
    codes = difflib.SequenceMatcher(a=str1, b=str2).get_opcodes()
    for code in codes:
        if code[0] == "equal":
            result += blue(str1[code[1] : code[2]])
        elif code[0] == "delete":
            result += delete_color(str1[code[1] : code[2]])
        elif code[0] == "insert":
            result += insert_color(str2[code[3] : code[4]])
        elif code[0] == "replace":
            result += delete_color(str1[code[1] : code[2]]) + insert_color(
                str2[code[3] : code[4]]
            )
    return result


def quote(val) -> str:
    return f"'{val}'"


def color_diff_list(list1, list2) -> str:
    result = []

    try:
        codes = difflib.SequenceMatcher(a=list1, b=list2).get_opcodes()
    except TypeError as e:
        logging.error(f"list1:\n{util.pretty_print(list1)}")
        logging.error(f"list2:\n{util.pretty_print(list2)}")
        raise e

    for code in codes:
        if code[0] == "equal":
            # result.extend(list1[code[1]:code[2]])
            result.extend(map(blue, list1[code[1] : code[2]]))
        elif code[0] == "delete":
            result.extend(map(red, list1[code[1] : code[2]]))
        elif code[0] == "insert":
            result.extend(map(green, list2[code[3] : code[4]]))
        elif code[0] == "replace":
            result.extend(map(red, list1[code[1] : code[2]]))
            result.extend(map(green, list2[code[3] : code[4]]))
    return "[" + ",\n\n".join(map(quote, result)) + "]"


# XXX: Add logic to ResultSet
def compare(rs1, rs2) -> bool:
    list1 = rs1.string_values() if rs1 else []
    list2 = rs2.string_values() if rs2 else []
    return sorted(list2) == sorted(list2)


def validate_html(html_dir, args, tidyrc) -> None:
    html_files = []
    for root, dirs, files in os.walk(html_dir):
        for file in files:
            if re.search(r"(?<!tidy)\.html$", file):
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
    if args.tidy and path_tidy:
        for file in html_files:
            ret = util.do_cmd(
                [path_tidy, "-config", tidyrc, file],
                allowed_returncodes=[1],
                stdout=PIPE,
                stderr=PIPE,
            )
            if ret:
                logging.debug(ret.stderr)
                indented_file = os.path.splitext(file)[0] + "-tidy.html"
                if args.indent and not os.path.exists(indented_file):
                    with open(indented_file, "w") as wfh:
                        wfh.write(ret.stdout)


def validate_xml(xml_file, schema_file) -> None:
    xmllint = shutil.which("xmllint")
    if xmllint:
        return util.do_cmd(
            [xmllint, "--noout", "--schema", schema_file, xml_file],
            stdout=PIPE,
            stderr=PIPE,
        )
    else:
        try:
            schema = ET.XMLSchema(ET.parse(schema_file))
            result = schema.validate(ET.parse(xml_file))
        except Exception as e:
            raise e


def load_thefuzz() -> None:
    for libname in ["fuzz", "process"]:
        try:
            lib = import_module(f"thefuzz.{libname}")
        except:
            logging.debug(sys.exc_info())
        else:
            globals()[libname] = lib


def get_term_width() -> int:
    try:
        term_size = os.get_terminal_size()
        term_width = term_size.columns
    except:
        term_width = 80
    return term_width


def format_vals(vals) -> str:
    if type(vals) is dict:
        return "\n".join([f"Line {k}: '{v}'" for k, v in vals.items()])
    else:
        # return repr(vals)
        return str(vals)


def passed_str(passed) -> str:
    status = "PASS" if passed else "FAIL"
    status = pass_color[passed](status)
    return status


def check_retval(retval, name) -> None:
    if retval is not None and not isinstance(retval, ResultSet):
        raise ValueError(
            f"Expected ResultSet for {name}, got {retval} instead."
        )


def validate_component(
    cid,
    comp_dir,
    config,
    basedir,
    lock,
) -> List[str]:
    errors = Errors(config.get("exit_on_error", False))

    global ead
    c = Component(ead.get_component(cid))

    logging.debug("----")
    logging.debug(c.id)
    logging.debug(c.level)
    logging.debug(c.title())
    logging.debug("\n")

    html_file = os.path.join(basedir, "contents", comp_dir, "index.html")
    logging.debug(f"HTML file: {html_file}")

    global ehtml_cache
    with lock:
        if html_file in ehtml_cache:
            logging.debug(f"Using existing EADHTML object for {html_file}.")
            ehtml = ehtml_cache[html_file]
        else:
            logging.debug(f"Adding {html_file} to EADHTML cache.")
            ehtml = EADHTML(html_file, parser=config["html_parser"])
            ehtml_cache[html_file] = ehtml

    try:
        chtml = ehtml.find_component(c.id)
    except ComponentNotFoundError as e:
        # errors.append(traceback.format_exc())
        errors.append(repr(e))
        return

    logging.debug(f"chtml id:     {chtml.id}")
    logging.debug(f"chtml level:  {chtml.level}")
    logging.debug(f"chtml title:  {chtml.title()}")
    logging.debug(f"chtml extent: {chtml.extent()}")

    logging.debug(f"component tag: {c.c.tag}")

    logging.info(f"Performing checks for component {c.id}")

    for method_name in config["checks"]["component"]:
        comp_method = getattr(c, method_name)

        logging.debug(f"calling Component.{method_name}()")
        args = []
        if method_name == "dao":
            args = [config["dao"]["valid-roles"]]
        comp_retval = comp_method(*args)
        logging.debug(f"retval={comp_retval}")
        check_retval(comp_retval, method_name)

        logging.debug(f"calling CompHTML.{method_name}()")
        chtml_method = getattr(chtml, method_name)
        args = []
        if method_name == "dao":
            args = [basedir, config["dao"]["valid-roles"]]
        chtml_retval = chtml_method(*args)
        logging.debug(f"retval={chtml_retval}")
        check_retval(chtml_retval, method_name)

        missing_err_template = (
            "Value not set for field '{}' in component"
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
                    comp_retval,
                    ead.ead_file,
                )
            )
        elif comp_retval is None and chtml_retval is not None:
            errors.append(
                missing_err_template.format(
                    method_name,
                    c.id,
                    "ead xml",
                    ead.ead_file,
                    chtml_retval,
                    html_file,
                )
            )
        else:
            passed_check = compare(comp_retval, chtml_retval)
            if not passed_check:
                errors.append(
                    f"field '{method_name}' differs for c id='{c.id}'\nDIFF:\n"
                    + f"{ead.ead_file}\n"
                    + f"{html_file}\n"
                    + diff(comp_values, chtml_values, config["diff"])
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

    return errors


def get_comp_dirs(elem, comp_dirs, depth, elem_dir, presentation_cids) -> None:
    for c in elem.component():
        if c.id in presentation_cids:
            c_dir = presentation_cids[c.id]
        elif depth == 0 and c.level in ["series", "otherlevel", "recordgrp"]:
            c_dir = c.id
        else:
            c_dir = elem_dir
        comp_dirs[c.id] = c_dir
        get_comp_dirs(c, comp_dirs, depth + 1, c_dir, presentation_cids)


def build_level_tree(elem, parent) -> None:
    for c in elem.component():
        child = Node((c.id, c.level), parent=parent)
        build_level_tree(c, child)


def render_level_tree(elem, root_name) -> List[str]:
    root = Node(root_name)
    build_level_tree(elem, root)
    return [f"{pre}{node.name}\n" for pre, fill, node in RenderTree(root)]


def read_config(config_file) -> dict:
    with open(config_file, "rb") as f:
        data = tomli.load(f)
    return data


def get_values(rs) -> ResultSet:
    return rs.string_values() if rs else None


def isnewer(file1, file2) -> bool:
    return os.stat(file1).st_mtime > os.stat(file2).st_mtime


def main() -> None:
    start_time = time.time()

    if not sys.version_info >= (3, 7):
        print("Python 3.7 or higher is required.")
        exit(1)

    script_dir = os.path.dirname(os.path.realpath(__file__))
    script_name = Path(__file__).stem

    parser = argparse.ArgumentParser(
        description="Validate finding aids html against ead xml file."
    )
    parser.add_argument("ead_file", metavar="EAD_FILE", help="ead file")
    parser.add_argument("html_dir", metavar="HTML_DIR", help="html directory")
    parser.add_argument(
        "--diff-type",
        default="simple",
        choices=["color", "unified", "unified-color", "simple"],
        help="diff type (default: %(default)s)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Verbose mode. Multiple -v options increase the verbosity."
            " The maximum is 3."
        ),
    )
    parser.add_argument(
        "-l",
        "--log-format",
        default=f"%(asctime)s - {script_name} - %(levelname)s - %(message)s",
        help="format for logging messages (default: %(default)s)",
    )
    parser.add_argument(
        "-t",
        "--tidy",
        action="store_true",
        help="Run HTML Tidy to test correctness of html",
    )
    parser.add_argument(
        "-i",
        "--indent",
        action="store_true",
        help="Indent XML with xsltproc.",
    )
    parser.add_argument(
        "--indent-dir",
        default=os.getcwd(),
        help=(
            "Directory where indented xml files are stored (default:"
            " %(default)s)"
        ),
    )
    parser.add_argument(
        "-b", "--broken-links", action="store_true", help="Find broken urls"
    )
    parser.add_argument(
        "-c", "--color", action="store_true", help="Enable color output"
    )
    parser.add_argument(
        "-p",
        "--progress-bar",
        action="store_true",
        help="Show progress bar for component checks",
    )
    parser.add_argument(
        "-e",
        "--exit-on-error",
        action="store_true",
        help="Exit script on first error",
    )
    parser.add_argument(
        "--html-parser",
        default="html5lib",
        choices=["html.parser", "html5lib"],
        help="HTML parser to be used by Beautiful Soup (default: %(default)s)",
    )
    parser.add_argument(
        "-m",
        "--multiprocessing",
        action="store_true",
        help="Parallelize component checks with multiple processes",
    )
    parser.add_argument(
        "--threading",
        action="store_true",
        help="Parallelize component checks with threads",
    )
    parser.add_argument(
        "--duration",
        action="store_true",
        help="Print rumtime duration as non-logging message",
    )
    args = parser.parse_args()

    if args.multiprocessing and args.threading:
        print("Can't set both --multiprocessing and --threading.")
        exit(1)

    global colors_enabled
    colors_enabled = args.color or "color" in args.diff_type

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

    logging.debug(f"Running Python {sys.version}")
    installed_pkgs = sorted(
        [f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set]
    )
    logging.debug(f"Installed packages: {pformat(installed_pkgs)}")

    config = read_config(os.path.join(script_dir, "config.toml"))
    logging.debug("config: %s", pformat(config))

    ead_file = os.path.abspath(args.ead_file)
    html_dir = os.path.abspath(args.html_dir)

    logging.debug("ead file: %s", ead_file)
    logging.debug("html dir: %s", html_dir)

    if args.indent_dir:
        pretty_ead_file = os.path.join(
            args.indent_dir, Path(ead_file).stem + "-pretty.xml"
        )
    else:
        pretty_ead_file = util.change_ext(ead_file, "-pretty.xml")
    indent_file = os.path.join(script_dir, "indent.xsl")
    xsltproc = shutil.which("xsltproc")
    if (
        args.indent
        and xsltproc
        and "pretty" not in ead_file
        and (
            not os.path.isfile(pretty_ead_file)
            or isnewer(ead_file, pretty_ead_file)
        )
    ):
        util.do_cmd(
            [xsltproc, "-o", pretty_ead_file, indent_file, ead_file],
            stdout=PIPE,
            stderr=PIPE,
        )

    schema_file = os.path.join(script_dir, "ead.xsd")
    validate_xml(ead_file, schema_file)

    tidyrc = os.path.join(script_dir, "tidyrc")
    validate_html(html_dir, args, tidyrc)

    global ead
    ead = Ead(ead_file)

    num_comp = ead.c_count()
    p = inflect.engine()
    p.num(num_comp)
    logging.info(f"The EAD has {p.no('component')}.")

    top_html_file = os.path.join(html_dir, "index.html")
    top_ehtml = EADHTML(top_html_file, parser=args.html_parser)

    logging.info(f"FASB Version: {top_ehtml.fasb_version()}")

    ead_date = ead.creation_date().values()[0]
    html_date = top_ehtml.creation_date().values()[0]
    if ead_date != html_date:
        print(f"Creation date mismatch: '{ead_date}' != '{html_date}'")
        exit(1)

    rqm_html_file = os.path.join(html_dir, "requestmaterials", "index.html")
    rqm = RequestMaterials(rqm_html_file, parser=args.html_parser)
    logging.debug(pformat(rqm.find_links()))

    all_html_file = os.path.join(html_dir, "all", "index.html")
    all_ehtml = EADHTML(all_html_file, parser=args.html_parser)

    load_thefuzz()

    term_width = get_term_width()

    config["diff"] = {
        "type": args.diff_type,
        "term_width": term_width,
        "sep": "-" * term_width,
    }

    config.update(vars(args))

    errors = Errors(config.get("exit_on_error", False))

    logging.info("Performing top level checks.")

    for method_name in config["checks"]["top-level"]:
        ead_method = getattr(ead, method_name)

        logging.debug(f"calling EAD.{method_name}()")
        ead_retval = ead_method()
        logging.debug(f"retval={ead_retval}")
        check_retval(ead_retval, method_name)

        logging.debug(f"calling EADHTML.{method_name}()")
        if method_name in config["all-html"]["fields"]:
            logging.debug("Using all html.")
            ehtml = all_ehtml
            html_file = all_html_file
        else:
            ehtml = top_ehtml
            html_file = top_html_file
        ehtml_method = getattr(ehtml, method_name)
        ehtml_retval = ehtml_method()
        logging.debug(f"retval={ehtml_retval}")
        check_retval(ehtml_retval, method_name)

        missing_err_template = (
            "Value not set for {} field '{}'"
            " inside file '{}' \nbut found"
            " values:\n{}\ninside '{}'"
        )

        passed_check = False
        if ead_retval is not None and ehtml_retval is None:
            errors.append(
                missing_err_template.format(
                    "html",
                    bold(method_name),
                    html_file,
                    ead_retval,
                    ead_file,
                )
            )
        elif ead_retval is None and ehtml_retval is not None:
            errors.append(
                missing_err_template.format(
                    "ead",
                    bold(method_name),
                    ead_file,
                    ehtml_retval,
                    html_file,
                )
            )
        else:
            passed_check = compare(ead_retval, ehtml_retval)
            if not passed_check:
                errors.append(
                    f"ead field '{method_name}' differs'\nDIFF:\n"
                    + f"{ead_file}\n"
                    + f"{html_file}\n"
                    + diff(ead_retval, ehtml_retval, config["diff"])
                )

        logging.info(f"{method_name}: [{passed_str(passed_check)}]")

    ead_comps = ead.component()
    ead_cids = [(c.id, c.level) for c in ead_comps]

    # html_cids = all_ehtml.component_id_level()
    html_comps = all_ehtml.component()
    html_cids = [(c.id, c.level) for c in html_comps]

    presentation_cids = {c.id: c.present_id for c in html_comps if c.present_id}

    logging.info("Performing nesting level check.")

    ead_tree = render_level_tree(ead, ead_file)
    ead_tree_str = "".join(ead_tree)
    logging.debug(f"EAD Nesting Level Tree\n{ead_tree_str}")

    html_tree = render_level_tree(all_ehtml, all_html_file)
    html_tree_str = "".join(html_tree)
    logging.debug(f"HTML Nesting Level Tree\n{html_tree_str}")

    passed_check = ead_tree[1:] == html_tree[1:]
    logging.info(f"nesting levels: [{passed_str(passed_check)}]")
    if not passed_check:
        errors.append(
            "Nesting error"
            + diff([ead_tree_str], [html_tree_str], config["diff"])
        )

    del all_ehtml, top_ehtml, rqm
    del ead_tree, ead_tree_str, html_tree, html_tree_str

    logging.debug(f"EAD CIDS {pformat(ead_cids)}")
    logging.debug(f"HTML CIDS {pformat(html_cids)}")
    logging.debug(f"Presentation CIDS {pformat(presentation_cids)}")

    if ead_cids != html_cids:
        errors.append(
            "Nesting level error at top"
            f" level:\nExpected:\n{pformat(ead_cids)}\nbut"
            f" got:\n{pformat(html_cids)}"
        )

    progress_bar = tqdm(total=ead.c_count()) if args.progress_bar else None

    global ehtml_cache
    ehtml_cache = EHTMLCache(maxsize=10)

    comp_dirs = {}
    get_comp_dirs(ead, comp_dirs, 0, "", presentation_cids)

    if args.multiprocessing or args.threading:
        try:
            num_cpus = len(os.sched_getaffinity(0))  # Only works on Unix
        except AttributeError:
            num_cpus = cpu_count()
        ishpc = "CLUSTER" in os.environ
        isslurm = any(env.startswith("SLURM") for env in os.environ)
        # hpc cluster reports large number of cpus which leads to a large
        # number of processes which may get killed by the os for lack of
        # resources. Limit to 2 except when running under slurm.
        if ishpc and not isslurm:
            num_cpus = 2

        if args.multiprocessing:
            exec_class_name = "ProcessPoolExecutor"
            exec_args = {
                "mp_context": get_context("fork"),  # needed for Macs
                "max_workers": num_cpus,
            }
            manager = Manager()
            lock = manager.Lock()
        else:
            exec_class_name = "ThreadPoolExecutor"
            exec_args = {"max_workers": min(32, num_cpus + 4)}
            lock = threading.Lock()

        logging.info(
            f"Using {exec_args['max_workers']} max workers for"
            f" {exec_class_name}."
        )

        exec_class = globals()[exec_class_name]

        with exec_class(**exec_args) as executor:
            tasks = {
                executor.submit(
                    validate_component,
                    cid,
                    comp_dirs[cid],
                    config,
                    html_dir,
                    lock,
                ): cid
                for cid in sorted(ead.all_component_ids())
            }

            for future in as_completed(tasks):
                cid = tasks[future]
                result = None
                try:
                    # print(f"future: {future}")
                    # print(f"component id: {cid}")
                    result = future.result()
                except SystemExit as e:
                    print(f"{cid} exited with value: {e}")
                except Exception as e:
                    print(f"{cid} failed with exception: {e}")
                else:
                    errors.extend(result)

                if result or result is None:
                    break
    else:
        from contextlib import nullcontext
        dummy_lock = nullcontext()

        for cid in sorted(ead.all_component_ids()):
            result = validate_component(
                cid, comp_dirs[cid], config, html_dir, dummy_lock
            )
            errors.extend(result)

    end_time = time.time()
    duration = util.format_duration(end_time - start_time)

    if errors:
        p.num(len(errors))
        print(f"There {p.plural_verb('is')} {p.no('error')}.")
        for error in errors:
            print(f"ERROR: {error}\n")

    print_method = print if args.duration else logging.info
    print_method(f"Validation complete in {duration}")
    exit(1 if errors else 0)


if __name__ == "__main__":
    main()
