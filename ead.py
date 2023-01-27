from collections import defaultdict
from lxml import etree as ET
from resultset import ResultSet
import component
import logging
import os.path
import re
import util


class Ead:
    def __init__(self, ead_file):
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
        no_ns_file = os.path.splitext(ead_file)[0] + "-no-ns.xml"
        self.tree.write(no_ns_file)

        logging.debug(self.root.tag)

    def __str__(self):
        return f"EAD({self.eadid}):\nurl = {self.url}\n"

    def abstract(self):
        return self.get_text("archdesc[@level='collection']/did/abstract")

    def accessrestrict(self):
        return self.get_text(
            "archdesc[@level='collection']/accessrestrict/*[not(self::head)]",
            join_text=True,
            sep="",
        )

    def accruals(self):
        return self.xpath("archdesc[@level='collection']/accruals/p")

    def acqinfo(self):
        return self.xpath("archdesc[@level='collection']/acqinfo/p")

    def altformavail(self):
        return self.get_archdesc("altformavail")

    def appraisal(self):
        return self.xpath("archdesc[@level='collection']/appraisal/p")

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
        return self.xpath("eadheader/filedesc/titlestmt/author")

    def bioghist(self):
        return self.get_text_join(
            "archdesc[@level='collection']/bioghist/p", sep=""
        )

    def c_count(self):
        return int(self.root.xpath("count(//c)"))

    def chronlist(self):
        expr = (
            "archdesc[@level='collection']/*[name() !="
            " 'dsc']//chronlist/chronitem"
        )
        chron_items = self.root.xpath(expr)
        if not chron_items:
            return None
        result = ResultSet(xpath=expr, value_type=dict)
        for item in chron_items:
            date = item.xpath("date")[0].text
            group = item.xpath("eventgrp")[0]
            events = []
            for event in group.xpath("event"):
                events.append(util.clean_text("".join(event.itertext())))
            result.add(item.tag, {date: events}, item.sourceline)
        return result

    def chronlist_heading(self):
        return self.xpath(
            "archdesc[@level='collection']/*[name()  !='dsc']//chronlist/head"
        )

    def collection(self):
        return self.unittitle()

    def collection_unitid(self):
        # return self.root.xpath("//archdesc/did/unitid")
        return self.unitid()

    def component(self):
        components = []
        for c in self.root.xpath("//c[not(ancestor::c)]"):
            components.append(component.Component(c, self))
        return components

    def corpname(self):
        return self.get_archdesc_nodsc("corpname")

    def creation_date(self):
        return self.xpath(
            "/ead/eadheader[1]/profiledesc[1]/creation[1]/date[1]"
        )

    def creator(self):
        creators = ResultSet()
        for field in ["corpname", "famname", "persname"]:
            expr = (
                "archdesc[@level='collection']/did/origination[@label='Creator'"
                f" or @label='source']/{field}"
            )
            result = self.xpath(expr)
            if result:
                creators.append(result)
        return creators

    def creators(self):
        creator_tags = ["corpname", "famname", "persname"]
        creator_expr = " or ".join(
            [f"name() = '{tag}'" for tag in creator_tags]
        )
        logging.debug(creator_expr)
        creator_xpath = (
            "archdesc[@level='collection']/did/"
            "origination[@label='Creator' or"
            f" @label='source']/*[{creator_expr}]"
        )
        logging.debug(creator_xpath)
        return self.get_text(creator_xpath)

    def custodhist(self):
        return self.xpath("archdesc[@level='collection']/custodhist/p")

    def dao(self):
        return self.get_text("//dao")

    def eadid(self):
        return self.xpath("eadheader/eadid")

    def famname(self):
        return self.get_archdesc_nodsc("famname")

    def function(self):
        return self.get_archdesc_nodsc("function")

    def genreform(self):
        return self.get_archdesc_nodsc_join("genreform")

    def geogname(self):
        return self.get_archdesc_nodsc_join("geogname")

    def get_archdesc(self, field):
        return self.xpath(f"archdesc[@level='collection']/{field}/p")

    def get_archdesc_nodsc(self, field, **kwargs):
        return util.xpath(
            self.root,
            f"archdesc[@level='collection']/*[name() != 'dsc']//{field}",
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
        return self.xpath(expr, all_text=True, **kwargs)

    def get_text_join(self, expr, **kwargs):
        return util.xpath(
            self.root, expr, all_text=True, join_text=True, **kwargs
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
        return self.xpath("//langusage/language/@langcode")

    def language(self):
        return self.xpath("//langusage/language")

    def material_type(self):
        return self.get_text_join_semi("//genreform")

    def name(self):
        return self.get_archdesc_nodsc("name")

    def names(self):
        names = ResultSet(sort=True)
        result = self.xpath("//*[local-name()!='repository']/corpname")
        if result:
            names.append(result)
        fields = ["famname", "persname"]
        for field in fields:
            result = self.xpath(f"//{field}")
            if result:
                names.append(result)
        return names

    def note(self):
        return self.xpath("eadheader/filedesc/notestmt/note/p")

    def occupation(self):
        return self.get_archdesc_nodsc("occupation")

    def persname(self):
        return self.get_archdesc_nodsc("persname")

    def phystech(self):
        return self.xpath("archdesc[@level='collection']/phystech/p")

    def place(self):
        return self.get_text_join_semi("//geogname")

    def prefercite(self):
        return self.get_text("archdesc[@level='collection']/prefercite/p")

    def repository(self):
        return self.get_archdesc_nodsc("repository")

    def scopecontent(self):
        return self.get_text_join(
            "archdesc[@level='collection']/scopecontent/p"
        )

    def separatedmaterial(self):
        return self.get_archdesc("separatedmaterial")

    def sponsor(self):
        return self.xpath("eadheader/filedesc/titlestmt/sponsor")

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
        return self.xpath("//titlestmt/subtitle")

    def title(self):
        return self.get_archdesc_nodsc("title")

    def unitdate(self, expr):
        return self.xpath(f"archdesc[@level='collection']/did/unitdate{expr}")

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
        return self.xpath("archdesc[@level='collection']/did/unitid")

    def unittitle(self):
        return self.xpath("archdesc[@level='collection']/did/unittitle")

    def url(self):
        return self.xpath("eadheader/eadid/@url")

    def userestrict(self):
        return self.get_archdesc("userestrict")

    def xpath(
        self, expr, all_text=False, join_text=False, sep=" ", join_sep=" "
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
                if attrib not in node.attrib:
                    continue
                text = node.get(attrib)
            elif all_text:
                words = []
                for itext in node.itertext():
                    words.append(itext)
                text = util.clean_text(sep.join(words))
            else:
                text = util.clean_text(node.text or "")
            result.add(node.tag, text, node.sourceline)

        if join_text and result:
            result = result.join(join_sep)

        return result if result else None

    #     def unitdate_parse(self, expr):
    #         dates = self.root.xpath(
    #             f"archdesc[@level='collection']/did/unitdate{expr}"
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
