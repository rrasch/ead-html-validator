EAD_FIELDS = """
creator
author
abstract
""".split()

COMP_FIELDS = """
unititle
""".split()

XLINK_NS = "http://www.w3.org/1999/xlink"

LONGTEXT_TAGS = ["p", "list", "chronlist"]
LONGTEXT_XPATH = (
    "*[" + " or ".join([f"self::{tag}" for tag in LONGTEXT_TAGS]) + "]"
)

DEFAULT_HEADINGS = {
    "accessrestrict": "Conditions Governing Access",
}
