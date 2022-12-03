from lxml import etree as ET
import constants as cs
import logging
import re
import util


class Component:
    def __init__(self, c, parent):
        self.c = c
        self.parent = parent
        self.ead_file = parent.ead_file

    def accessrestrict(self):
        return self.get_val("accessrestrict/p")

    def accessrestrict_heading(self):
        return self.get_text("accessrestrict/head")

    def accruals(self):
        return self.get_val("accruals/p")

    def accruals_heading(self):
        return self.get_val("accruals/head")

    def acqinfo(self):
        return self.get_val("acqinfo/p")

    def acqinfo_heading(self):
        return self.get_val("acqinfo/head")

    def altformavail(self):
        return self.get_val("altformavail/p")

    def altformavail_heading(self):
        return self.get_val("altformavail/head")

    def appraisal(self):
        return self.get_val("appraisal/p")

    def appraisal_heading(self):
        return self.get_val("appraisal/head")

    def arrangement(self):
        return self.get_val("arrangement/p")

    def arrangement_heading(self):
        return self.get_val("arrangement/head")

    def bioghist(self):
        return self.get_val("bioghist/p")

    def bioghist_heading(self):
        return self.get_val("bioghist/head")

    def corpname(self):
        return self.get_val("controlaccess/corpname")

    def creator(self):
        # return self.get_text("did/origination[@label='Creator']")
        return self.get_text(
            "did/origination[@label='Creator']/*[substring(name(),"
            " string-length(name()) - string-length('name') + 1) = 'name']",
            sep=None
        )

    def custodhist(self):
        return self.get_val("custodhist/p")

    def custodhist_heading(self):
        return self.get_val("custodhist/head")

    def _dao(self, return_list=False):
        for node in self.c.xpath("did"):
            logging.debug(ET.tostring(node, pretty_print=True).decode())
        dao_list = self.c.xpath("did/*[self::dao or self::daogrp]")
        if return_list:
            return dao_list
        else:
            return dao_list[0]

    def dao_desc(self):
        for node in self.c.xpath("did"):
            logging.debug(ET.tostring(node, pretty_print=True).decode())
        return self.get_val("did/*[self::dao or self::daogrp]/daodesc/p")

    def dao_link(self):
        link_list = []
        links = self.c.xpath(f"did/*[self::dao or self::daogrp]//@*[local-name()='href']")

        if links:
            return sorted(list(map(str, links)))
        else:
            return None

    def dao_title(self):
        title = self.c.xpath(f"did/*[self::dao or self::daogrp]/@*[local-name()='title']")
        if title:
            return str(title[0])
        else:
            return None

    def dimensions(self):
        return self.get_text("did/physdesc/dimensions")

    def extent(self):
        return self.get_text("did/physdesc/extent")

    def famname(self):
        return self.get_text("controlaccess/famname")

    def fileplan(self):
        return self.get_val("fileplan/p")

    def fileplan_heading(self):
        return self.get_val("fileplan/head")

    def function(self):
        return self.get_val("controlaccess/function")

    def genreform(self):
        return self.get_val("controlaccess/genreform")

    def geogname(self):
        return self.get_val("controlaccess/geogname")

    def get_text(self, xpath_expr, sep=" "):
        nodes = self.c.xpath(xpath_expr)
        if not nodes:
            return None
        text_list = [" ".join(node.itertext()) for node in nodes]
        if sep is None:
            return [util.clean_text(text) for text in text_list]
        else:
            return util.clean_text(sep.join(text_list))

    def get_val(self, xpath_expr):
        value = self.c.xpath(xpath_expr)
        if value:
            return re.sub(r"\s+", " ", value[0].text).strip()
        else:
            return None

    def id(self):
        return self.c.attrib["id"]

    def langcode(self):
        return self.get_val("did/langmaterial/language/@langcode")

    def language(self):
        return self.get_text("did/langmaterial/language")

    def level(self):
        return self.c.attrib["level"]

    def name(self):
        pass

    def occupation(self):
        return self.get_val("controlaccess/occupation")

    def odd(self):
        return self.get_text("odd/p")

    def odd_heading(self):
        return self.get_text("odd/head")

    def originalsloc(self):
        return self.get_val("originalsloc/p")

    def originalsloc_heading(self):
        return self.get_val("originalsloc/head")

    def otherfindaid(self):
        return self.get_val("otherfindaid/p")

    def otherfindaid_heading(self):
        return self.get_val("otherfindaid/head")

    def persname(self):
        return self.get_val("controlaccess/persname")

    def physfacet(self):
        return self.get_val("did/physdesc/physfacet")

    def physloc(self):
        return self.get_text("did/physloc", "; ")

    def phystech(self):
        return self.get_val("phystech/p")

    def phystech_heading(self):
        return self.get_val("phystech/head")

    def prefercite(self):
        return self.get_val("prefercite/p")

    def prefercite_heading(self):
        return self.get_val("prefercite/head")

    def processinfo(self):
        return self.get_val("processinfo/p")

    def processinfo_heading(self):
        return self.get_val("processinfo/head")

    def relatedmaterial(self):
        return self.get_val("relatedmaterial/p")

    def relatedmaterial_heading(self):
        return self.get_val("relatedmaterial/head")

    def separatedmaterial(self):
        return self.get_text("separatedmaterial/p")

    def separatedmaterial_heading(self):
        return self.get_val("separatedmaterial/head")

    def scopecontent(self):
        return self.get_val("scopecontent/p")

    def scopecontent_heading(self):
        return self.get_val("scopecontent/head")

    def sub_components(self):
        sub_comps = []
        for child in self.c:
            if child.tag == "c":
                sub_comps.append(Component(child, self))
        return sub_comps

    def subject(self):
        return self.get_val("controlaccess/subject")

    def title(self):
        return self.unittitle()

    def unitdate(self):
        return self.get_val("did/unitdate")

    def unitid(self):
        return self.get_val("did/unitid")

    def unittitle(self):
        return self.get_text("did/unittitle")

    def userestrict(self):
        return self.get_val("userestrict/p")

    def userestrict_heading(self):
        return self.get_val("userestrict/head")
