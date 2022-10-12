from bs4 import BeautifulSoup
import logging
import re


class CompHTML:
    def __init__(self, c, id):
        self.c = c
        self.id_ = id

    def __str__(self):
        # return str(self.c)
        return self.c.prettify()

    def id(self):
        return self.id_

    def level(self):
        # div = self.c.find_all("div", class_=re.compile('^level'))[0]
        # lvl = div['class'][0].split('-')[1]
        if (
            self.c.name == "div"
            and self.c.has_attr("class")
            and self.c["class"][0].startswith("level")
        ):
            lvl = self.c["class"][0].split("-")[1]
        else:
            lvl = None
        return lvl

    def title(self):
        return self.c.find(re.compile("h\d"), class_="unittitle").text

    #     def unitdate(self):
    #         return ""
    #
    #     def corpname(self):
    #         return ""
    #
    #     def famname(self):
    #         return ""
    #
    #     def genreform(self):
    #         return ""
    #
    #     def geogname(self):
    #         return ""
    #
    #     def name(self):
    #         return ""
    #
    #     def persname(self):
    #         return ""
    #
    #     def subject(self):
    #         return ""

    #     def dimenison(self):
    #         return self.c.xpath("did/physdesc/dimensions")[0].text
    #
    #     def langcode(self):
    #         return self.c.xpath("did/langmaterial/language/@langcode")[0].text
    #
    #     def language(self):
    #         return self.c.xpath("did/langmaterial")[0].text
    #
    #     def unittitle(self):
    #         return self.c.find(re.compile('h\d'), class_='unittitle').text
    #
    #     def accessrestrict(self):
    #         return self.c.xpath("accessrestrict/p")[0].text
    #
    #     def accessrestrict_heading(self):
    #         return self.c.xpath("accessrestrict/head")[0].text
    #
    #     def accruals(self):
    #         return self.c.xpath("accruals/p")[0].text
    #
    #     def accruals_heading(self):
    #         return self.c.xpath("accruals/head")[0].text
    #
    #     def acqinfo(self):
    #         return self.c.xpath("acqinfo/p")[0].text
    #
    #     def acqinfo_heading(self):
    #         return self.c.xpath("acqinfo/head")[0].text
    #
    #     def altformavail(self):
    #         return self.c.xpath("altformavail/p")[0].text
    #
    #     def altformavail_heading(self):
    #         return self.c.xpath("altformavail/head")[0].text
    #
    #     def appraisal(self):
    #         return self.c.xpath("appraisal/p")[0].text
    #
    #     def appraisal_heading(self):
    #         return self.c.xpath("appraisal/head")[0].text
    #
    #     def arrangement(self):
    #         return self.c.xpath("arrangement/p")[0].text
    #
    #     def arrangement_heading(self):
    #         return self.c.xpath("arrangement/head")[0].text
    #
    #     def custodhist(self):
    #         return self.c.xpath("custodhist/p")[0].text
    #
    #     def custodhist_heading(self):
    #         return self.c.xpath("custodhist/head")[0].text

    def extent(self):
        return self.physdesc("extent")

    #     def fileplan(self):
    #         return self.c.xpath("fileplan/p")[0].text
    #
    #     def fileplan_heading(self):
    #         return self.c.xpath("fileplan/head")[0].text
    #
    #     def originalsloc(self):
    #         return self.c.xpath("originalsloc/p")[0].text
    #
    #     def originalsloc_heading(self):
    #         return self.c.xpath("originalsloc/head")[0].text

    def physdesc(self, field):
        phys_desc = self.c.find("div", class_=re.compile("physdesc"))
        if not phys_desc:
            return None
        header = phys_desc.find(re.compile("h\d"), class_=re.compile(field))
        sib = header.find_next_sibling("div")
        print(sib)
        return sib.text


#     def phystech(self):
#         return self.c.xpath("phystech/p")[0].text
#
#     def phystech_heading(self):
#         return self.c.xpath("phystech/head")[0].text
#
#     def processinfo(self):
#         return self.c.xpath("processinfo/p")[0].text
#
#     def processinfo_heading(self):
#         return self.c.xpath("processinfo/head")[0].text
#
#     def relatedmaterial(self):
#         return self.c.xpath("relatedmaterial/p")[0].text
#
#     def relatedmaterial_heading(self):
#         return self.c.xpath("relatedmaterial/head")[0].text
#
#     def separatedmaterial(self):
#         return self.c.xpath("separatedmaterial/p")[0].text
#
#     def separatedmaterial_heading(self):
#         return self.c.xpath("separatedmaterial/head")[0].text
#
#     def scopecontent(self):
#         return self.c.xpath("scopecontent/p")[0].text
#
#     def scopecontent_heading(self):
#         return self.c.xpath("scopecontent/head")[0].text
#
#     def userestrict(self):
#         return self.c.xpath("userestrict/p")[0].text
#
#     def userestrict_heading(self):
#         return self.c.xpath("userestrict/head")[0].text
