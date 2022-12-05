from lxml import etree as ET
import component
import logging
import util


class Ead:
    def __init__(self, ead_file):
        logging.debug(f"ead_file={ead_file}")
        self.ead_file = ead_file

        nsmap = {"e": "urn:isbn:1-931666-22-9"}

        self.tree = ET.parse(ead_file)
        logging.debug(self.tree)

        self.root = self.tree.getroot()
        logging.debug(self.root)

        util.remove_namespace(self.root, nsmap["e"])
        logging.debug(self.root)

        logging.debug(self.root.tag)

    def __str__(self):
        return f"EAD({self.eadid}):\nurl = {self.url}\n"

    def abstract(self):
        node = self.root.xpath("archdesc[@level='collection']/did/abstract")[0]
        for t in node.itertext():
            logging.debug(f"text='{t}'")
        text = "".join(node.itertext())
        return " ".join(text.split())
        # return util.stringify_children(node)

    def acqinfo(self):
        return self.root.xpath("archdesc[@level='collection']/acqinfo/p")[
            0
        ].text

    def altformavail(self):
        return self.get_archdesc("altformavail")

    def appraisal(self):
        return self.root.xpath("archdesc[@level='collection']/appraisal/p")[
            0
        ].text

    def author(self):
        author_val = self.root.xpath("eadheader/filedesc/titlestmt/author")[
            0
        ].text
        return_list = False
        if return_list:
            return re.split(r"\s*\,\s*", author_val)
        else:
            return author_val

    def bioghist(self):
        return self.root.xpath("archdesc[@level='collection']/bioghist/p")[
            0
        ].text

    def chronlist(self):
        items = {}
        chron_items = self.root.xpath(
            "archdesc[@level='collection']/*[name() !="
            " 'dsc']//chronlist/chronitem"
        )
        for item in chron_items:
            date = item.xpath("date")[0].text
            group = item.xpath("eventgrp")[0]
            events = []
            for event in group.xpath("event"):
                events.append(util.clean_text("".join(event.itertext())))
            items[date] = events
        return items

    def chronlist_heading(self):
        return util.clean_text(
            self.root.xpath(
                "archdesc[@level='collection']/*[name()"
                " !='dsc']//chronlist/head"
            )[0].text
        )


    def collection(self):
        return self.unittitle()

    def collection_unitid(self):
        # return self.root.xpath("//archdesc/did/unitid")
        return self.unitid()

    def component(self):
        components = []
        for c in self.root.xpath("//c[not(ancestor::c)]"):
            # logging.debug(c.attrib['id'])
            # logging.debug(c.attrib['level'])
            components.append(component.Component(c, self))
        return components

    def corpname(self):
        return_list = True
        return self.get_archdesc_nodsc("corpname", return_list)

    def creation_date(self):
        return util.clean_text(
            self.root.xpath(
                "/ead/eadheader[1]/profiledesc[1]/creation[1]/date[1]"
            )[0].text
        )

    def creator(self):
        creators = []
        for field in ["corpname", "famname", "persname"]:
            for node in self.root.xpath(
                "archdesc[@level='collection']/did/"
                "origination[@label='Creator'"
                f" or @label='source']/{field}"
            ):
                logging.debug(node)
                creators.append(node.text.strip())
        logging.debug(creators)
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
        return self.root.xpath("archdesc[@level='collection']/custodhist/p")[
            0
        ].text

    def dao(self):
        return self.get_text("//dao")

    def eadid(self):
        return self.root.xpath("eadheader/eadid")[0].text

    def famname(self):
        return self.get_archdesc_nodsc("famname", return_list=True)

    def function(self):
        return self.get_archdesc_nodsc("function")

    def genreform(self):
        return self.get_archdesc_nodsc("genreform")

    def geogname(self):
        return self.get_archdesc_nodsc("geogname")

    def get_archdesc(self, field):
        return self.root.xpath(f"archdesc[@level='collection']/{field}/p")[
            0
        ].text

    def get_archdesc_nodsc(self, field, return_list=False):
        nodes = self.root.xpath(
            f"archdesc[@level='collection']/*[name() != 'dsc']//{field}"
        )
        values = set()
        for node in nodes:
            # logging.debug(util.clean_text("".join(node.itertext())))
            # values.add(node.text)
            # values.add("".join(node.itertext()).strip())
            values.add(util.clean_text("".join(node.itertext())))

        if return_list:
            return list(values)
        else:
            return ", ".join(list(values))

    def get_text(self, expr, return_list=True):
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
        return self.root.xpath("//langusage/language/@langcode")[0]

    def language(self):
        return self.root.xpath("//langusage/language")[0].text

    def material_type(self):
        return self.get_text("//genreform")

    def name(self):
        return self.get_archdesc_nodsc("name", return_list=True)

    def names(self):
        names = set(self.get_text("//*[local-name()!='repository']/corpname"))
        fields = ["famname", "persname"]
        for field in fields:
            name_list = self.get_text(f"//{field}")
            names.update(name_list)
        return sorted(list(names))

    def note(self):
        return self.root.xpath("eadheader/filedesc/notestmt/note/p")[0].text

    def occupation(self):
        return self.get_archdesc_nodsc("occupation")

    def persname(self):
        return self.get_archdesc_nodsc("persname", return_list=True)

    def phystech(self):
        return self.root.xpath("archdesc[@level='collection']/phystech/p")[
            0
        ].text

    def place(self):
        places = set()
        for geo in self.root.xpath("//geogname"):
            places.add(" ".join(geo.text.split()))
        return list(places)

    def prefercite(self):
        return self.root.xpath("archdesc[@level='collection']/prefercite/p")[
            0
        ].text

    def repository(self):
        return self.get_archdesc_nodsc("repository")

    def scopecontent(self):
        return self.root.xpath("archdesc[@level='collection']/scopecontent/p")[
            0
        ].text

    def separatedmaterial(self):
        return self.get_archdesc("separatedmaterial")

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
        return self.root.xpath("//titlestmt/subtitle")[0].text

    def title(self):
        return self.get_archdesc_nodsc("title", return_list=True)

    def unitdate(self, expr):
        xpath = f"archdesc[@level='collection']/did/unitdate{expr}"
        dates = self.root.xpath(xpath)
        return [
            util.clean_text(
                str(date)
                if isinstance(date, ET._ElementUnicodeResult)
                else date.text
            )
            for date in dates
        ]

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
        return self.root.xpath("archdesc[@level='collection']/did/unitid")[
            0
        ].text

    def unittitle(self):
        return self.root.xpath("archdesc[@level='collection']/did/unittitle")[
            0
        ].text

    def url(self):
        return str(self.root.xpath("eadheader/eadid/@url")[0])

    def userestrict(self):
        return self.get_archdesc("userestrict")

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
