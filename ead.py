from collections import defaultdict
from constants import LONGTEXT_XPATH
from lxml import etree as ET
from pprint import pprint
from resultset import ResultSet
import component
import logging
import os.path
import re
import util


class Ead:
    def __init__(self, ead_file, save_no_ns=False):
        logging.debug(f"ead_file={ead_file}")
        self.ead_file = ead_file

        nsmap = {
            "e": "urn:isbn:1-931666-22-9",
            "xlink": "http://www.w3.org/1999/xlink",
        }

        self.tree = ET.parse(ead_file)
        logging.debug(self.tree)

        self.root = self.tree.getroot()
        logging.debug(self.root)

        for namespace in nsmap.values():
            util.remove_namespace(self.root, namespace)
            logging.debug(self.root)

        ET.cleanup_namespaces(self.tree)
        if save_no_ns:
            no_ns_file = os.path.splitext(ead_file)[0] + "-no-ns.xml"
            self.tree.write(no_ns_file)

        logging.debug(self.root.tag)

        self._set_archdesc_xpath()

    def __str__(self):
        return f"EAD({self.eadid}):\nurl = {self.url}\n"

    def abstract(self):
        return self.get_text(f"{self.archdesc_xpath}/did/abstract")

    def accessrestrict(self):
        return self.get_text(
            f"{self.archdesc_xpath}/accessrestrict/*[not(self::head)]",
        )

    def accruals(self):
        return self.get_text(f"{self.archdesc_xpath}/accruals/p")

    def acqinfo(self):
        return self.get_text(f"{self.archdesc_xpath}/acqinfo/p")

    def altformavail(self):
        return self.get_archdesc("altformavail")

    def appraisal(self):
        return self.get_text(f"{self.archdesc_xpath}/appraisal/p")

    def _author(self):
        expr = "eadheader/filedesc/titlestmt/author"
        nodes = self.root.xpath("eadheader/filedesc/titlestmt/author")
        if not nodes:
            return None

        result = ResultSet(xpath=expr)
        for node in nodes:
            for author in re.split(r"\s*\,\s*", node.text):
                results.add(node.name, author, node.sourceline)
        return result

    def author(self):
        return self.get_text("eadheader/filedesc/titlestmt/author")

    def bioghist(self):
        return self.get_text_long(
            f"{self.archdesc_xpath}/bioghist/{LONGTEXT_XPATH}"
        )

    def c_count(self):
        return int(self.root.xpath("count(//c)"))

    def chronlist(self):
        expr = (
            f"{self.archdesc_xpath}/*[name() !="
            " 'dsc']//chronlist/chronitem"
        )
        chron_items = self.root.xpath(expr)
        if not chron_items:
            return None
        result = ResultSet(xpath=expr, value_type=dict)
        for item in chron_items:
            date = item.xpath("date")[0].text.strip()
            date = " ".join(date.split())
            events = []
            for event in item.xpath(".//event"):
                events.append(util.clean_text("".join(event.itertext())))
            result.add(item.tag, {date: events}, item.sourceline)
        return result

    def chronlist_heading(self):
        return self.get_text(
            f"{self.archdesc_xpath}/*[name()  !='dsc']//chronlist/head"
        )

    def collection(self):
        return self.unittitle()

    def collection_unitid(self):
        return self.unitid()

    def get_component(self, cid):
        c = self.root.xpath(f"//c[@id='{cid}']")
        return c[0] if c else None

    def component(self):
        components = []
        for c in self.root.xpath("//c[not(ancestor::c)]"):
            components.append(component.Component(c, self))
        return components

    def all_components(self):
        return [component.Component(c, self) for c in self.root.xpath("//c")]

    def all_component_ids(self):
        return [c.get("id") for c in self.root.xpath("//c")]

    def corpname(self):
        return self.get_archdesc_nodsc("corpname")

    def creation_date(self):
        return self.get_text(
            "/ead/eadheader[1]/profiledesc[1]/creation[1]/date[1]"
        )

    def creator(self):
        creators = ResultSet()
        for field in ["corpname", "famname", "persname"]:
            expr = (
                f"{self.archdesc_xpath}/did/origination[@label='Creator'"
                f" or @label='source']/{field}"
            )
            result = self.xpath(expr)
            if result:
                creators.append(result)
        return creators if creators else None

    def creators(self):
        creator_tags = ["corpname", "famname", "persname"]
        creator_expr = " or ".join(
            [f"name() = '{tag}'" for tag in creator_tags]
        )
        logging.debug(creator_expr)
        creator_xpath = (
            f"{self.archdesc_xpath}/did/"
            "origination[@label='Creator' or"
            f" @label='source']/*[{creator_expr}]"
        )
        logging.debug(creator_xpath)
        return self.get_text(creator_xpath)

    def custodhist(self):
        return self.get_text_long(f"{self.archdesc_xpath}/custodhist/p")

    def dao(self):
        return self.get_text("//dao")

    def eadid(self):
        return self.get_text("eadheader/eadid")

    def famname(self):
        return self.get_archdesc_nodsc("famname")

    def function(self):
        return self.get_archdesc_nodsc("function")

    def genreform(self):
        return self.get_archdesc_nodsc("genreform")

    def geogname(self):
        return self.get_archdesc_nodsc("geogname")

    def get_archdesc(self, field, tag="p"):
        return self.get_text(f"{self.archdesc_xpath}/{field}/{tag}")

    def get_archdesc_nodsc(self, field, **kwargs):
        return util.xpath(
            self.root,
            f"{self.archdesc_xpath}/*[name() != 'dsc']//{field}",
            all_text=True,
            **kwargs,
        )

    def get_archdesc_nodsc_join(self, field, **kwargs):
        return self.get_archdesc_nodsc(
            field,
            # all_text=True,
            join_text=True,
            join_sep="; ",
            **kwargs
        )

    def get_text(self, expr, **kwargs):
        return util.xpath(self.root, expr, all_text=True, **kwargs)

    def get_text_ignore_space(self, expr, **kwargs):
        return util.xpath(
            self.root, expr, all_text=True, ignore_space=True, **kwargs
        )

    def get_text_join(self, expr, **kwargs):
        return util.xpath(
            self.root, expr, all_text=True, join_text=True, **kwargs
        )

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

    def get_text_join_semi(self, expr, **kwargs):
        return util.xpath(
            self.root,
            expr,
            all_text=True,
            join_text=True,
            join_sep="; ",
            **kwargs,
        )

    def get_text_no_lineno(self, expr, return_list=True):
        node_text_list = set()

        for node in self.root.xpath(expr):
            words = []
            for text in node.itertext():
                words.extend(text.split())
            node_text_list.add(" ".join(words))

        if return_list:
            return list(node_text_list)
        else:
            return ", ".join(list(node_text_list))

    def heading(self):
        return self.unittitle()

    def langcode(self):
        return self.get_text(
            "eadheader/profiledesc/langusage/language/@langcode"
        )

    def language(self):
        return self.get_text("eadheader/profiledesc/langusage/language")

    def langusage(self):
        return self.get_text("eadheader/profiledesc/langusage")

    def materialspec(self):
        return self.get_text(f"{self.archdesc_xpath}/did/materialspec")

    def material_type(self):
        return self.get_text("//genreform")

    def name(self):
        return self.get_archdesc_nodsc("name")

    def names(self):
        names = ResultSet(sort=True)
        result = self.get_text("//*[local-name() != 'repository']/corpname")
        if result:
            names.append(result)
        fields = ["famname", "persname"]
        for field in fields:
            result = self.xpath(f"//{field}")
            if result:
                names.append(result)
        return names if names else None

    def note(self):
        return self.get_text("eadheader/filedesc/notestmt/note/p")

    def occupation(self):
        return self.get_archdesc_nodsc("occupation")

    def originalsloc(self):
        return self.get_archdesc("originalsloc")

    def persname(self):
        return self.get_archdesc_nodsc("persname")

    def phystech(self):
        return self.get_text(f"{self.archdesc_xpath}/phystech/p")

    def place(self):
        return self.get_text("//geogname")

    def prefercite(self):
        return self.get_text(f"{self.archdesc_xpath}/prefercite/p")

    def repository(self):
        return self.get_archdesc_nodsc("repository")

    def scopecontent(self):
        return self.get_text_long(
            f"{self.archdesc_xpath}/scopecontent/{LONGTEXT_XPATH}",
        )

    def separatedmaterial(self):
        return self.get_archdesc("separatedmaterial", LONGTEXT_XPATH)

    def _set_archdesc_xpath(self):
        self.archdesc_xpath = None
        for level in ["collection", "series"]:
            xpath = f"(archdesc[@level='{level}'])[1]"
            if self.root.xpath(xpath):
                self.archdesc_xpath = xpath
                break
        if not self.archdesc_xpath:
            raise ValueError("Can't")

    def sponsor(self):
        return self.get_text("eadheader/filedesc/titlestmt/sponsor")

    def subject(self):
        return self.get_archdesc_nodsc("subject")

    def subjects(self):
        return self.get_text(
            """
            //*[not(ancestor::c) and (local-name()='subject' or
                                      local-name()='function' or
                                      local-name()='occupation')]
            """
        )

    def subtitle(self):
        return self.get_text("//titlestmt/subtitle")

    def title(self):
        return self.get_archdesc_nodsc("title")

    def unitdate(self, expr):
        return self.get_text(f"{self.archdesc_xpath}/did/unitdate{expr}")

    def unitdate_all(self):
        return self.unitdate("")

    def _unitdate_bulk(self):
        return self.unitdate("[@type='bulk']")

    def _unitdate_inclusive(self):
        return self.unitdate("[@type='inclusive']")

    def _unitdate_normal(self):
        return self.unitdate("/@normal")

    def _unitdate_not_type(self):
        return self.unitdate("[not(@type)]")

    def unitid(self):
        return self.get_text(f"{self.archdesc_xpath}/did/unitid")

    def unittitle(self):
        return self.get_text(f"{self.archdesc_xpath}/did/unittitle")

    def url(self):
        return self.get_text("eadheader/eadid/@url")

    def userestrict(self):
        return self.get_archdesc("userestrict")

    def xpath(
        self, expr, all_text=False, join_text=False, sep="", join_sep=" "
    ):
        attrib = None
        match = re.search(r"(/@([A-Za-z]+))$", expr)
        if match:
            attrib = match.group(2)
            expr = re.sub(rf"{match.group(1)}$", "", expr)

        nodes = self.root.xpath(expr)
        if not nodes:
            return None

        total_text = ""
        result = ResultSet(xpath=expr)
        for node in nodes:
            if attrib:
                text = node.get(attrib)
            elif all_text:
                words = []
                for itext in node.itertext():
                    words.append(itext)
                text = util.clean_text(sep.join(words)) if words else None
            else:
                text = util.clean_text(node.text) if node.text else None

            if not text:
                continue

            result.add(node.tag, text, node.sourceline)

        if join_text and result:
            result = result.join(join_sep)

        return result if result else None

    #     def unitdate_parse(self, expr):
    #         dates = self.root.xpath(
    #             f"{self.archdesc_xpath}/did/unitdate{expr}"
    #         )
    #         return [date.text for date in dates]

    #     def date_range(self):
    #         return self.root.xpath("get_date_range_facets,")
    #
    #     def unitdate_start(self):
    #         return self.root.xpath("start_dates.compact,")
    #
    #     def unitdate_end(self):
    #         return self.root.xpath("end_dates.compact,")
    #
    #     def unitdate(self):
    #         return self.root.xpath("ead_date_display,")
    #
    #
    #     def parent_unittitles(self):
    #         return self.root.xpath("parent_unittitle_list(node)")

    #     def series(self):
    #         return self.root.xpath("")
