from lxml import etree as ET
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
    
    def __str__(self):
        return (
            f"Leader({self.ldr_str}):\n"
            f"record length {self.record_len}\n"
            f"record status = {self.record_status}\n"
            f"record type = {self.record_type}\n"
            f"bib level = {self.bib_level}\n"
            f"control type = {self.control_type}\n"
            f"char_coding_scheme = {self.char_coding_scheme}\n"
        )

    def eadid(self):
        return self.root.xpath("eadheader/eadid")[0].text

    def author(self):
        authors = []
        for node in self.root.xpath("eadheader/filedesc/titlestmt/author"):
            authors.append(node.text)
        return authors

    def unittitle(self):
        return self.root.xpath("archdesc[@level='collection']/did/unittitle")[0].text

    def unitid(self):
        return self.root.xpath("archdesc[@level='collection']/did/unitid")[0].text

    def abstract(self):
        find_text = ET.XPath("//text()")
        node = self.root.xpath("archdesc[@level='collection']/did/abstract")[0]
        #return ' '.join([t for t in node.itertext()])
        return util.stringify_children(node)

#     def creator(self):
#         return self.root.xpath("archdesc[@level='collection']/did/origination[@label='creator']/*[#{creator_fields_to_return self.root.xpath}]")

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
# 
#     def scopecontent(self):
#         return self.root.xpath("archdesc[@level='collection']/scopecontent/p")
# 
#     def bioghist(self):
#         return self.root.xpath("archdesc[@level='collection']/bioghist/p")
# 
#     def acqinfo(self):
#         return self.root.xpath("archdesc[@level='collection']/acqinfo/p")
# 
#     def custodhist(self):
#         return self.root.xpath("archdesc[@level='collection']/custodhist/p")
# 
#     def appraisal(self):
#         return self.root.xpath("archdesc[@level='collection']/appraisal/p")
# 
#     def phystech(self):
#         return self.root.xpath("archdesc[@level='collection']/phystech/p")
# 
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

