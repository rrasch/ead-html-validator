#!/usr/bin/env python3


from fuzzywuzzy import fuzz
from fuzzywuzzy import process

import argparse
import constants
import ead
import eadhtml
import inspect
import logging
import os.path
import time
import util


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
    ehtml = eadhtml.EADHTML(html_file)
    chtml = ehtml.find_component(c.id())
    print(chtml)
    print(chtml.id())
    print(chtml.level())
    print(chtml.title())
    print("extent: %s" % chtml.extent())

    for sub_c in c.sub_components():
        # print(sub_c)
        # print(sub_c.id())
        # print(sub_c.level())
        validate_component(sub_c, new_dirpath)


def main():

    logging.basicConfig(
        format="%(asctime)s - ead-validator - %(levelname)s - %(message)s",
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

    ead_methods = []
    for attr in dir(my_ead):
        obj = getattr(my_ead, attr)

        if attr.startswith("_") or not callable(obj):
            continue

        if len(inspect.signature(obj).parameters) > 0:
            continue

        ead_methods.append(attr)


    for method_name, ead_method in util.get_methods(my_ead).items():
        # ehtml_method = getattr(ehtml, method_name)

        logging.debug(f"calling ead.{method_name}()")
        ead_retval = ead_method()
        logging.debug(f"retval={ead_retval}")

        # logging.debug(f"calling eadhtml.{method_name}()")
        # ehtml_retval = ehtml_method()
        # print(f"retval={ehtml_retval}")

    # for c in my_ead.component():
    #     validate_component(c, args.html_dir)


if __name__ == "__main__":
    main()

