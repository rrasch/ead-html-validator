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

    def eadid(self):
        return self.root.xpath("eadheader/eadid")[0].text

    def author(self):
        results = self.soup.find_all("div", class_="author")
        return results[0].div.get_text()

    def unittitile(self):
        return None

    def unitid(self):
        return self.soup.find_all("div", class_="unit_id")[0].div.get_text()

    def creator(self):
        creators = []
        for node in self.soup.find_all(
            "div", class_=re.compile("(corp|fam|pers)name role-Donor")
        ):
            creator = node.get_text()
            creators.append(creator)
        return creators

    def unitdate_normal(self):
        return self.root.xpath(
            "archdesc[@level='collection']/did/unitdate/@normal"
        )

    #     def unitdate(self):
    #         return self.root.xpath("archdesc[@level='collection']/did/unitdate[not(@type)]")
    #
    #     def unitdate_bulk(self):
    #         return self.root.xpath("archdesc[@level='collection']/did/unitdate[@type='bulk']")
    #
    #     def unitdate_inclusive(self):
    #         return self.root.xpath("archdesc[@level='collection']/did/unitdate[@type='inclusive']")


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
        items = []
        clist = self.soup.find("span", class_="ead-chronlist")
        for item in clist.find("span", class_="ead-chronitem"):
            print(item.get_text())
            items.append(item.get_text())
        logging.debug(items)
        exit(1)

#     def corpname(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//corpname")
#
#     def famname(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//famname")
#
#     def function(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//function")
#
#     def genreform(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//genreform")
#
#     def geogname(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//geogname")
#
#     def name(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//name")
#
#     def occupation(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//occupation")
#
#     def persname(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//persname")
#
#     def subject(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//subject")
#
#     def title(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//title")
#
#     def note(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//note")
#
#     def repository(self):
#         return self.root.xpath("ENV['EAD'].split("\/")[-1]")
#
#     def format(self):
#         return self.root.xpath("Archival Collection")
#
#     def format(self):
#         return self.root.xpath("0")
#
#     def creator(self):
#         return self.root.xpath("//*[local-name()!='repository']/corpname")
#
#     def (self):
#         return self.root.xpath("//*[local-name()!='repository']/famname")
#
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
#     def place(self):
#         return self.root.xpath("//geogname")
#
#     def subject(self):
#         return self.root.xpath("//*[local-name()='subject' or local-name()='function' or local-name() = 'occupation']")
#
#     def dao(self):
#         return self.root.xpath("//dao")
#
#     def material_type(self):
#         return self.root.xpath("//genreform")
#
#     def heading(self):
#         return self.root.xpath("unittitle")
#
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
#     def language(self):
#         return self.root.xpath("language,")
#
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
#
#     def collection(self):
#         return self.root.xpath("//archdesc/did/unittitle")
#
#     def collection_unitid(self):
#         return self.root.xpath("//archdesc/did/unitid")
#
#     def chronlist(self):
#         return self.root.xpath("")
#
#     def series(self):
#         return self.root.xpath("")
