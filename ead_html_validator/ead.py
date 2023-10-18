from collections import defaultdict
from ead_html_validator.component import Component
from ead_html_validator.constants import LONGTEXT_XPATH
from ead_html_validator.resultset import ResultSet
from lxml import etree as ET
from typing import List
import ead_html_validator.util as util
import logging
import os.path
import re


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

    def __str__(self) -> str:
        return f"EAD({self.eadid}):\nurl = {self.url}\n"

    def abstract(self) -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/did/abstract")

    def accessrestrict(self) -> ResultSet:
        return self.get_text(
            f"{self.archdesc_xpath}/accessrestrict/*[not(self::head)]",
        )

    def accruals(self) -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/accruals/p")

    def acqinfo(self) -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/acqinfo/p")

    def altformavail(self) -> ResultSet:
        return self.get_archdesc("altformavail")

    def appraisal(self) -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/appraisal/p")

    def _author(self) -> ResultSet:
        expr = "eadheader/filedesc/titlestmt/author"
        nodes = self.root.xpath("eadheader/filedesc/titlestmt/author")
        if not nodes:
            return None

        result = ResultSet(xpath=expr)
        for node in nodes:
            for author in re.split(r"\s*\,\s*", node.text):
                results.add(node.name, author, node.sourceline)
        return result

    def author(self) -> ResultSet:
        return self.get_text("eadheader/filedesc/titlestmt/author")

    def bioghist(self) -> ResultSet:
        return self.get_text_long(
            f"{self.archdesc_xpath}/bioghist/{LONGTEXT_XPATH}"
        )

    def c_count(self) -> int:
        return int(self.root.xpath("count(//c)"))

    def chronlist(self) -> ResultSet:
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

    def chronlist_heading(self) -> ResultSet:
        return self.get_text(
            f"{self.archdesc_xpath}/*[name()  !='dsc']//chronlist/head"
        )

    def collection(self) -> ResultSet:
        return self.unittitle()

    def collection_unitid(self) -> ResultSet:
        return self.unitid()

    def get_component(self, cid) -> ET._Element:
        c = self.root.xpath(f"//c[@id='{cid}']")
        return c[0] if c else None

    def component(self) -> List[Component]:
        components = []
        for c in self.root.xpath("//c[not(ancestor::c)]"):
            components.append(Component(c, self))
        return components

    def all_components(self) -> List[Component]:
        return [Component(c, self) for c in self.root.xpath("//c")]

    def all_component_ids(self) -> List[str]:
        return [c.get("id") for c in self.root.xpath("//c")]

    def corpname(self) -> ResultSet:
        return self.get_archdesc_nodsc("corpname")

    def creation_date(self) -> ResultSet:
        return self.get_text(
            "/ead/eadheader[1]/profiledesc[1]/creation[1]/date[1]"
        )

    def creator(self) -> ResultSet:
        creators = ResultSet()
        for field in ["corpname", "famname", "persname"]:
            expr = (
                f"{self.archdesc_xpath}/did/origination[@label='Creator'"
                f" or @label='creator' or @label='source']/{field}"
            )
            result = self.xpath(expr)
            if result:
                creators.append(result)
        return creators if creators else None

    def creators(self) -> ResultSet:
        creator_tags = ["corpname", "famname", "persname"]
        creator_expr = " or ".join(
            [f"name() = '{tag}'" for tag in creator_tags]
        )
        logging.debug(creator_expr)
        creator_xpath = (
            f"{self.archdesc_xpath}/did/"
            "origination[@label='Creator' or @label='creator' or"
            f" @label='source']/*[{creator_expr}]"
        )
        logging.debug(creator_xpath)
        return self.get_text(creator_xpath)

    def custodhist(self) -> ResultSet:
        return self.get_text_long(f"{self.archdesc_xpath}/custodhist/p")

    def dao(self) -> ResultSet:
        return self.get_text("//dao")

    def eadid(self) -> ResultSet:
        return self.get_text("eadheader/eadid")

    def famname(self) -> ResultSet:
        return self.get_archdesc_nodsc("famname")

    def function(self) -> ResultSet:
        return self.get_archdesc_nodsc("function")

    def genreform(self) -> ResultSet:
        return self.get_archdesc_nodsc("genreform")

    def geogname(self) -> ResultSet:
        return self.get_archdesc_nodsc("geogname")

    def get_archdesc(self, field, tag="p") -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/{field}/{tag}")

    def get_archdesc_nodsc(self, field, **kwargs) -> ResultSet:
        return util.xpath(
            self.root,
            f"{self.archdesc_xpath}/*[name() != 'dsc']//{field}",
            all_text=True,
            **kwargs,
        )

    def get_archdesc_nodsc_join(self, field, **kwargs) -> ResultSet:
        return self.get_archdesc_nodsc(
            field,
            # all_text=True,
            join_text=True,
            join_sep="; ",
            **kwargs
        )

    def get_text(self, expr, **kwargs) -> ResultSet:
        return util.xpath(self.root, expr, all_text=True, **kwargs)

    def get_text_ignore_space(self, expr, **kwargs) -> ResultSet:
        return util.xpath(
            self.root, expr, all_text=True, ignore_space=True, **kwargs
        )

    def get_text_join(self, expr, **kwargs) -> ResultSet:
        return util.xpath(
            self.root, expr, all_text=True, join_text=True, **kwargs
        )

    def get_text_long(self, expr, **kwargs) -> ResultSet:
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

    def get_text_join_semi(self, expr, **kwargs) -> ResultSet:
        return util.xpath(
            self.root,
            expr,
            all_text=True,
            join_text=True,
            join_sep="; ",
            **kwargs,
        )

    def get_text_no_lineno(self, expr, return_list=True) -> ResultSet:
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

    def heading(self) -> ResultSet:
        return self.unittitle()

    def langcode(self) -> ResultSet:
        return self.get_text(
            "eadheader/profiledesc/langusage/language/@langcode"
        )

    def language(self) -> ResultSet:
        return self.get_text("eadheader/profiledesc/langusage/language")

    def langusage(self) -> ResultSet:
        return self.get_text("eadheader/profiledesc/langusage")

    def materialspec(self) -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/did/materialspec")

    def material_type(self) -> ResultSet:
        return self.get_text("//genreform")

    def name(self) -> ResultSet:
        return self.get_archdesc_nodsc("name")

    def names(self) -> ResultSet:
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

    def note(self) -> ResultSet:
        return self.get_text("eadheader/filedesc/notestmt/note/p")

    def occupation(self) -> ResultSet:
        return self.get_archdesc_nodsc("occupation")

    def originalsloc(self) -> ResultSet:
        return self.get_archdesc("originalsloc")

    def persname(self) -> ResultSet:
        return self.get_archdesc_nodsc("persname")

    def phystech(self) -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/phystech/p")

    def place(self) -> ResultSet:
        return self.get_text("//geogname")

    def prefercite(self) -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/prefercite/p")

    def repository(self) -> ResultSet:
        return self.get_archdesc_nodsc("repository")

    def scopecontent(self) -> ResultSet:
        return self.get_text_long(
            f"{self.archdesc_xpath}/scopecontent/{LONGTEXT_XPATH}",
        )

    def separatedmaterial(self) -> ResultSet:
        return self.get_archdesc("separatedmaterial", LONGTEXT_XPATH)

    def _set_archdesc_xpath(self) -> None:
        self.archdesc_xpath = None
        for level in ["collection", "series"]:
            xpath = f"(archdesc[@level='{level}'])[1]"
            if self.root.xpath(xpath):
                self.archdesc_xpath = xpath
                break
        if not self.archdesc_xpath:
            raise ValueError("Can't")

    def sponsor(self) -> ResultSet:
        return self.get_text("eadheader/filedesc/titlestmt/sponsor")

    def subject(self) -> ResultSet:
        return self.get_archdesc_nodsc("subject")

    def subjects(self) -> ResultSet:
        return self.get_text(
            """
            //*[not(ancestor::c) and (local-name()='subject' or
                                      local-name()='function' or
                                      local-name()='occupation')]
            """
        )

    def subtitle(self) -> ResultSet:
        return self.get_text("//titlestmt/subtitle")

    def title(self) -> ResultSet:
        return self.get_archdesc_nodsc("title")

    def unitdate(self, expr) -> ResultSet:
        date_xpath = f"{self.archdesc_xpath}/did/unitdate{expr}"
        unitdates = ResultSet(xpath=date_xpath)

        for date in self.root.xpath(date_xpath):
            val = date.text.strip()
            if val:
                val = util.clean_date(val)
                if "type" in date.attrib:
                    val += ", " + date.get("type")
            elif "normal" in date.attrib:
                val = date.get("normal")
                val = util.clean_date_normal(val)

            if val:
                unitdates.add(date.tag, val, date.sourceline)

        return unitdates.join(uniq=False, sep="; ") if unitdates else None

    def unitdate_all(self) -> ResultSet:
        return self.unitdate("[@datechar='creation']")

    def _unitdate_bulk(self) -> ResultSet:
        return self.unitdate("[@type='bulk']")

    def _unitdate_inclusive(self) -> ResultSet:
        return self.unitdate("[@type='inclusive']")

    def _unitdate_normal(self) -> ResultSet:
        return self.unitdate("/@normal")

    def _unitdate_not_type(self) -> ResultSet:
        return self.unitdate("[not(@type)]")

    def unitid(self) -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/did/unitid[not(@type)]")

    def unittitle(self) -> ResultSet:
        return self.get_text(f"{self.archdesc_xpath}/did/unittitle")

    def url(self) -> ResultSet:
        return self.get_text("eadheader/eadid/@url")

    def userestrict(self) -> ResultSet:
        return self.get_archdesc("userestrict")

    def xpath(
        self, expr, all_text=False, join_text=False, sep="", join_sep=" "
    ) -> ResultSet:
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
