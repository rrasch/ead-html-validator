from lxml import etree as ET
import component
import logging
import util

class Ead:

    def __init__(self, ead_file):
        print(f"ead_file={ead_file}")

        nsmap = {"e": "urn:isbn:1-931666-22-9"}

        self.tree = ET.parse(ead_file)
        logging.debug(self.tree)
        self.root = self.tree.getroot()
        logging.debug(self.root)
        util.remove_namespace(self.root, nsmap['e'])
        logging.debug(self.root)

        logging.debug(self.root.tag)
   
    def get_archdesc(self, field):
        return self.root.xpath(f"archdesc[@level='collection']/{field}/p")[0].text

    def get_archdesc_nodsc(self, field):
        nodes = self.root.xpath(f"archdesc[@level='collection']/*[name() != 'dsc']//{field}")
        values = set()
        for node in nodes:
            values.add(node.text)
        #return list(values)
        return ', '.join(list(values))

    def __str__(self):
        return (
            f"EAD({self.eadid}):\n"
            f"url = {self.url}\n"
        )

    def eadid(self):
        return self.root.xpath("eadheader/eadid")[0].text

    def url(self):
        return self.root.xpath("eadheader/eadid/@url")[0]

    def author(self):
        authors = []
        for node in self.root.xpath("eadheader/filedesc/titlestmt/author"):
            authors.append(node.text)
        return authors

    def unittitle(self):
        return self.root.xpath("archdesc[@level='collection']/did/unittitle")[0].text

    def unitid(self):
        return self.root.xpath("archdesc[@level='collection']/did/unitid")[0].text

    def langcode(self):
        #return self.root.xpath("archdesc[@level='collection']/did/langmaterial/language/@langcode")[0].text
        return self.root.xpath("//langusage/language/@langcode")[0]

    def language(self):
        return self.root.xpath("//langusage/language")[0].text

    def abstract(self):
        find_text = ET.XPath("//text()")
        node = self.root.xpath("archdesc[@level='collection']/did/abstract")[0]
        for t in node.itertext():
            print(f"text='{t}'")
        text = ''.join(node.itertext())
        return ' '.join(text.split())
        #return util.stringify_children(node)
        #return ""

    def creator(self):
        creators = []
        for field in ['corpname', 'famname', 'persname']:
            for node in self.root.xpath(f"archdesc[@level='collection']/did/origination[@label='Creator' or @label='creator']/{field}"):
                print(node)
                creators.append(node.text.strip())
        print(creators)
        return creators

    def unitdate_normal(self):
        return self.root.xpath("archdesc[@level='collection']/did/unitdate/@normal")

    def unitdate(self):
        return self.root.xpath("archdesc[@level='collection']/did/unitdate[not(@type)]")

    def unitdate_bulk(self):
        return self.root.xpath("archdesc[@level='collection']/did/unitdate[@type='bulk']")

    def unitdate_inclusive(self):
        return self.root.xpath("archdesc[@level='collection']/did/unitdate[@type='inclusive']")

    def acqinfo(self):
        return self.root.xpath("archdesc[@level='collection']/acqinfo/p")[0].text

    def appraisal(self):
        return self.root.xpath("archdesc[@level='collection']/appraisal/p")[0].text

    def bioghist(self):
        return self.root.xpath("archdesc[@level='collection']/bioghist/p")[0].text

    def custodhist(self):
        return self.root.xpath("archdesc[@level='collection']/custodhist/p")[0].text

    def phystech(self):
        return self.root.xpath("archdesc[@level='collection']/phystech/p")[0].text

    def prefercite(self):
        return self.root.xpath("archdesc[@level='collection']/prefercit/p")[0].text

    def scopecontent(self):
        return self.root.xpath("archdesc[@level='collection']/scopecontent/p")[0].text

    def separatedmaterial(self):
        return self.get_archdesc("separatedmaterial")
    
    def userestrict(self):
        return self.get_archdesc("userestrict")

    def chronlist(self):
        return self.root.xpath("archdesc[@level='collection']/*[name() != 'dsc']//chronlist/chronitem//text()")

    def corpname(self):
        return self.get_archdesc_nodsc('corpname')

    def famname(self):
        return self.get_archdesc_nodsc('famname')

    def function(self):
        return self.get_archdesc_nodsc('function')

    def genreform(self):
        return self.get_archdesc_nodsc('genreform')

    def geogname(self):
        return self.get_archdesc_nodsc('geogname')

    def name(self):
        return self.get_archdesc_nodsc('name')

    def note(self):
        return self.get_archdesc_nodsc('note')

    def occupation(self):
        return self.get_archdesc_nodsc('occupation')

    def persname(self):
        return self.get_archdesc_nodsc('persname')

    def subject(self):
        return self.get_archdesc_nodsc('subject')

    def title(self):
        return self.get_archdesc_nodsc('title')

#     def repository(self):
#         return self.root.xpath("ENV['EAD'].split("\/")[-1]")
# 
#     def format(self):
#         return self.root.xpath("Archival Collection")
# 
#     def format(self):
#         return self.root.xpath("0")

#     def creator(self):
#         creator = []
#         return self.root.xpath("//*[local-name()!='repository']/corpname")
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

    def place(self):
        #return self.root.xpath("//geogname")
        return self.get_archdesc_nodsc('geogname')

#     def subject(self):
#         return self.root.xpath("//*[local-name()='subject' or local-name()='function' or local-name() = 'occupation']")
# 
#     def dao(self):
#         return self.root.xpath("//dao")
# 
    def material_type(self):
        #return self.root.xpath("//genreform")
        return self.get_archdesc_nodsc('geogname')

    def heading(self):
        #return self.root.xpath("unittitle")
        return self.unittile()

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

    def collection(self):
        #eturn self.root.xpath("//archdesc/did/unittitle")
        return unittitle()

    def collection_unitid(self):
        #return self.root.xpath("//archdesc/did/unitid")
        return self.unitid()

#     def series(self):
#         return self.root.xpath("")

    def component(self):
        components = []
        for c in self.root.xpath("//c[not(ancestor::c)]"):
            print(c.attrib['id'])
            print(c.attrib['level'])
            components.append(component.Component(c))
        return components

