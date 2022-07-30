from bs4 import BeautifulSoup
import logging
import re

class EADHTML:

    def __init__(self, html_file):
        logging.debug(f"html_file={html_file}")
        self.soup = BeautifulSoup(open(html_file), 'html.parser')

    def find_component(self, id):
        return self.soup.find_all(re.compile('h\d'), id=id)[0].parent

    def get_formatted_note(self, field):
        return self.soup.find_all('div', class_=f'formattednote {field}')[0].div.p.get_text()

    def eadid(self):
        return self.root.xpath("eadheader/eadid")[0].text

    def author(self):
        results = self.soup.find_all('div', class_='author')
        return results[0].div.get_text()

    def unittitile(self):
        return None

    def unitid(self):
        return self.soup.find_all('div', class_='unit_id')[0].div.get_text()

    def creator(self):
        creators = []
        for node in self.soup.find_all('div', class_=re.compile('(corp|fam|pers)name role-Donor')):
            creator = node.get_text()
            creators.append(creator)
        return creators

    def unitdate_normal(self):
        return self.root.xpath("archdesc[@level='collection']/did/unitdate/@normal")

#     def unitdate(self):
#         return self.root.xpath("archdesc[@level='collection']/did/unitdate[not(@type)]")
# 
#     def unitdate_bulk(self):
#         return self.root.xpath("archdesc[@level='collection']/did/unitdate[@type='bulk']")
# 
#     def unitdate_inclusive(self):
#         return self.root.xpath("archdesc[@level='collection']/did/unitdate[@type='inclusive']")

# <div class="formattednote abstract" id ="aspace_ref3">
# <div class="formattednote accessrestrict" id ="aspace_7737a7dc7fd92d0055945aaca8066375">
# <div class="formattednote accruals" id ="aspace_f05011cc547339bd4114711751029c6d">
# <div class="formattednote acqinfo" id ="aspace_7be31470c64f6cfbf4336ba9af1a31d3">
# <div class="formattednote appraisal" id ="aspace_45cf36d965d0f038d67621dbebb9ebf1">
# <div class="formattednote arrangement" id ="aspace_65d23a620677d7f70a9b3dcfa9523829">
# <div class="formattednote bibliography" id ="aspace_4eace9a22f9f43be89b214957dbba587">
# <div class="formattednote bioghist" id ="aspace_5bfa9f2060a4b600e0b0ae6c3924354b">
# <div class="formattednote custodhist" id ="aspace_03c962dea0c06463b3615c01bc8ac97e">
# <div class="formattednote dimensions">
# <div class="formattednote editionstmt" >
# <div class="formattednote extent">
# <div class="formattednote notestmt">
# <div class="formattednote odd" id ="aspace_0c2299264bc16498d16857b8d48c6626">
# <div class="formattednote physfacet">
# <div class="formattednote phystech" id ="aspace_6535a00a00c94c0593f378d76d4dec87">
# <div class="formattednote prefercite" id ="aspace_3a758dcc0a9eafb7976839a96615fa21">
# <div class="formattednote processinfo" id ="aspace_ede025697b8e5bd48a2e9752bb4eb634">
# <div class="formattednote relatedmaterial" id ="aspace_5234804138e0f9a3a4639042d816b7f4">
# <div class="formattednote revisiondesc"><h3 class="label formattednote-header">Revisions to this Guide</h3>
# <div class="formattednote scopecontent" id ="aspace_c2e115638fa0f6448f8a05f567287451">
# <div class="formattednote separatedmaterial" id ="aspace_93d92d0c1e70183fc245965ea55d1a8b">
# <div class="formattednote userestrict" id ="aspace_2d8e669a800c026aefc9d7e76ca578c9">

    def abstract(self):
        results = self.soup.find_all('div', class_='formattednote abstract')
        return results[0].p.get_text()

    def accessrestrict(self):
        return self.get_formatted_note('accessrestrict')

    def accruals(self):
        return self.get_formatted_note('accruals')

    def acqinfo(self):
        return self.get_formatted_note('acqinfo')

    def appraisal(self):
        return self.get_formatted_note('appraisal')

    def arrangement(self):
        return self.get_formatted_note('arrangement')

    def bibliography(self):
        return self.get_formatted_note('bibliography')

    def bioghist(self):
        return self.soup.find_all('div', class_='formattednote bioghist')[0].div.p.get_text()

    def custodhist(self):
        return self.get_formatted_note('custodhist')

    def dimensions(self):
        return self.get_formatted_note('dimensions')

    def editionstmt(self):
        return self.get_formatted_note('editionstmt')

    def extent(self):
        return self.soup.find_all('div', class_='formattednote extent')[0].div.get_text()

    def notestmt(self):
        return self.get_formatted_note('notestmt')

    def odd(self):
        return self.get_formatted_note('odd')

    def physfacet(self):
        return self.get_formatted_note('physfacet')

    def phystech(self):
        return self.get_formatted_note('phystech')

    def prefercite(self):
        return self.get_formatted_note('prefercite')

    def relatedmaterial(self):
        return self.get_formatted_note('relatedmaterial')

    def revisiondesc(self):
        return self.get_formatted_note('revisiondesc')

    def scopecontent(self):
        return self.soup.find_all('div', class_='formattednote scopecontent')[0].div.p.get_text()

    def separatedmaterial(self):
        return self.get_formatted_note('separatedmaterial')

    def userestrict(self):
        return self.get_formatted_note('userestrict')
 
#     def chronlist(self):
#         return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//chronlist/chronitem//text()")
# 
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

