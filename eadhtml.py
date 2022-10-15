from bs4 import BeautifulSoup
import comphtml
import logging
import re


class EADHTML:
    def __init__(self, html_file):
        logging.debug(f"html_file={html_file}")
        self.soup = BeautifulSoup(open(html_file), "html.parser")
        self.html_file = html_file

    def find_component(self, id):
        return comphtml.CompHTML(
            self.soup.find_all(re.compile("h\d"), id=id)[0].parent, id
        )

    def get_formatted_note(self, field):
        note = self.soup.find_all("div", class_=f"md-group formattednote {field}")[0]
        #text = note.div.p.get_text()
        text = note.find('p').get_text()
        return text

    def eadnum(self):
        return self.soup.find("span", class_="ead-num").get_text()

    def url(self):
        return self.soup.find("link", rel="canonical")["href"]

    def eadid(self):
        return self.url().rstrip("/").split("/")[-1]

    def author(self):
        results = self.soup.find_all("div", class_="author")
        return results[0].div.get_text()

    def unittitile(self):
        return None

    def unitid(self):
        return self.soup.find("div", class_="md-group unit_id").div.get_text()

    def creator(self):
        creators = []
        for node in self.soup.find_all(
            "div", class_=re.compile("(corp|fam|pers)name role-Donor")
        ):
            creator = node.get_text()
            creators.append(creator)
        return creators

    def creators(self):
        return self.creator()

    def unitdate_normal(self):
        pass

    #     def unitdate(self):
    #         return self.root.xpath("archdesc[@level='collection']/did/unitdate[not(@type)]")
    #
    def unitdate_bulk(self):
        pass

    def unitdate_inclusive(self):
        pass

    def root(self):
        pass

    def abstract(self):
        logging.debug(self.html_file)
        return self.get_formatted_note("abstract")

    def accessrestrict(self):
        return self.get_formatted_note("accessrestrict")

    def accruals(self):
        return self.get_formatted_note("accruals")

    def acqinfo(self):
        return self.get_formatted_note("acqinfo")

    def appraisal(self):
        return self.get_formatted_note("appraisal")

    def arrangement(self):
        return self.get_formatted_note("arrangement")

    def bibliography(self):
        return self.get_formatted_note("bibliography")

    def bioghist(self):
        return self.get_formatted_note("bioghist")

    def custodhist(self):
        return self.get_formatted_note("custodhist")

    def dimensions(self):
        return self.get_formatted_note("dimensions")

    def editionstmt(self):
        return self.get_formatted_note("editionstmt")

    def extent(self):
        return self.get_formatted_note("extent")

    def note(self):
        return self.notestmt()

    def notestmt(self):
        return self.get_formatted_note("notestmt")

    def odd(self):
        return self.get_formatted_note("odd")

    def physfacet(self):
        return self.get_formatted_note("physfacet")

    def phystech(self):
        return self.get_formatted_note("phystech")

    def processinfo(self):
        return self.get_formatted_note("processinfo")

    def prefercite(self):
        return self.get_formatted_note("prefercite")

    def relatedmaterial(self):
        return self.get_formatted_note("relatedmaterial")

    def revisiondesc(self):
        return self.get_formatted_note("revisiondesc")

    def scopecontent(self):
        return self.get_formatted_note("scopecontent")

    def separatedmaterial(self):
        return self.get_formatted_note("separatedmaterial")

    def userestrict(self):
        return self.get_formatted_note("userestrict")

    def chronlist(self):
        items = {}
        clist = self.soup.find("span", class_="ead-chronlist")
        for item in clist.find_all("span", class_="ead-chronitem"):
            date = item.find("span", class_="ead-date").get_text()
            group = item.find("span", class_="ead-eventgrp")
            events = [ event.get_text() for event in group.find_all("span", class_="ead-event") ]
            items[date] = events
        return items

    def control_access_group(self, field):
        group = self.soup.find("div", class_=f"controlaccess-{field}-group")
        return [ div.get_text() for div in group.find_all("div") ]

    def corpname(self):
        return self.control_access_group("corpname")

    def famname(self):
        return list(self.soup.find("div", class_=re.compile("^famname")).stripped_strings)[0]

    def function(self):
        return self.control_access_group("function")

    def genreform(self):
        return self.control_access_group("genreform")

    def geogname(self):
        return self.control_access_group("geogname")

    def name(self):
        return "TODO"

    def names(self):
        return "TODO"

    def occupation(self):
        return self.control_access_group("occupation")

    def persname(self):
        return self.control_access_group("persname")

    def subject(self):
        return self.control_access_group("subject")

    def title(self):
        return self.title.text

    def repository(self):
        pass

#     def (self):
#         return self.root.xpath("//*[local-name()!='repository']/persname")
#
#     def name(self):
#         return self.root.xpath("//*[local-name()!='repository']/corpname")
#
#     def (self):
#         return self.root.xpath("//famname")
#
#     def (self):
#         return self.root.xpath("//persname")
#
    def place(self):
        pass

#     def subject(self):
#         return self.root.xpath("//*[local-name()='subject' or local-name()='function' or local-name() = 'occupation']")

    def dao(self):
        pass

    def material_type(self):
        return self.genreform()

    def heading(self):
        return self.unittitle()

    def langcode(self):
        return self.language()

#     def date_range(self):
#         return self.root.xpath("get_date_range_facets,")
#
#     def unitdate_start(self):
#         return self.root.xpath("start_dates.compact,")
#
#     def unitdate_end(self):
#         return self.root.xpath("end_dates.compact,")

    def unitdate(self):
        pass

    def language(self):
        return self.soup.find("div", class_="langusage").span.text

#     def id(self):
#         return self.root.xpath("//eadid + node.attr(“id”)")
#
#     def ead(self):
#         return self.root.xpath("//eadid")
#
#     def parent(self):
#         return self.root.xpath("node.parent.attr("id")")
#
#     def parent(self):
#         return self.root.xpath("parent_id_list(node)")
#
#     def parent_unittitles(self):
#         return self.root.xpath("parent_unittitle_list(node)")
#
#     def component_level(self):
#         return self.root.xpath("parent_id_list(node).length + 1")
#
#     def component_children(self):
#         return self.root.xpath("component_children?(node)")

    def unittitle(self):
        return self.soup.main.find(re.compile("h\d"), class_="page-title").get_text()

    def collection(self):
        return self.unittitle()

    def collection_unitid(self):
        return self.unitid()

    def component(self):
        return "TODO"

#     def series(self):
#         return self.root.xpath("")
