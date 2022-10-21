#!/usr/bin/env -S python3 -u


from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from pathlib import Path
import argparse
import constants
import ead
import eadhtml
import functools
import inspect
import logging
import os.path
import re
import time
import util


print = functools.partial(print, flush=True)


def compare(val1, val2):
    if type(val1) is not list:
        val1 = [val1]
    if type(val2) is not list:
        val2 = [val2]
    return val1 == val2


def validate(xml_file):
    return util.do_cmd(["xmllint", "--noout", "--schema", "ead.xsd", xml_file])


def validate_component(c, dirpath):

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
    chtml = ehtml.find_component(c.id())
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

        chtml_method = getattr(chtml, method_name)
        logging.debug(f"calling CompHTML.{method_name}()")
        chtml_retval = chtml_method()
        logging.debug(f"retval={chtml_retval}")

    for sub_c in c.sub_components():
        # print(sub_c)
        # print(sub_c.id())
        # print(sub_c.level())
        validate_component(sub_c, new_dirpath)


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

    validate(args.ead_file)

    my_ead = ead.Ead(args.ead_file)

    html_file = os.path.join(args.html_dir, "index.html")
    ehtml = eadhtml.EADHTML(html_file)

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

        if not compare(ead_retval, ehtml_retval):
            errors.append(f"{ead_retval} != {ehtml_retval}")

        if ehtml_retval is None:
            exit(1)

    for c in my_ead.component():
        validate_component(c, args.html_dir)

    for error in errors:
        print(f"ERROR: {error}")


if __name__ == "__main__":
    main()

