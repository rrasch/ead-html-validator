class Component:
    def __init__(self, c):
        self.c = c

    def get_val(self, xpath_expr):
        value = self.c.xpath(xpath_expr)
        if value:
            return (value[0].text or "").strip()
        else:
            return None

    def sub_components(self):
        sub_comps = []
        for child in self.c:
            if child.tag == "c":
                sub_comps.append(Component(child))
        return sub_comps

    def id(self):
        return self.c.attrib["id"]

    def level(self):
        return self.c.attrib["level"]

    def title(self):
        return self.unittitle()

    def unitid(self):
        return self.get_val("did/unitid")

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

    def dimenison(self):
        return self.get_val("did/physdesc/dimensions")

    def langcode(self):
        return self.get_val("did/langmaterial/language/@langcode")

    def language(self):
        return self.get_text("did/langmaterial")

    def get_text(self, xpath_expr):
        node = self.c.xpath(xpath_expr)
        if node is None:
            return None
        words = []
        for text in node[0].itertext():
            words.extend(text.split())
        return " ".join(words)

    def unittitle(self):
        return self.get_text("did/unittitle")

    def accessrestrict(self):
        return self.get_val("accessrestrict/p")

    def accessrestrict_heading(self):
        return self.get_val("accessrestrict/head")

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

    def custodhist(self):
        return self.get_val("custodhist/p")

    def custodhist_heading(self):
        return self.get_val("custodhist/head")

    def fileplan(self):
        return self.get_val("fileplan/p")

    def fileplan_heading(self):
        return self.get_val("fileplan/head")

    def originalsloc(self):
        return self.get_val("originalsloc/p")

    def originalsloc_heading(self):
        return self.get_val("originalsloc/head")

    def phystech(self):
        return self.get_val("phystech/p")

    def phystech_heading(self):
        return self.get_val("phystech/head")

    def processinfo(self):
        return self.get_val("processinfo/p")

    def processinfo_heading(self):
        return self.get_val("processinfo/head")

    def relatedmaterial(self):
        return self.get_val("relatedmaterial/p")

    def relatedmaterial_heading(self):
        return self.get_val("relatedmaterial/head")

    def separatedmaterial(self):
        return self.get_val("separatedmaterial/p")

    def separatedmaterial_heading(self):
        return self.get_val("separatedmaterial/head")

    def scopecontent(self):
        return self.get_val("scopecontent/p")

    def scopecontent_heading(self):
        return self.get_val("scopecontent/head")

    def userestrict(self):
        return self.get_val("userestrict/p")

    def userestrict_heading(self):
        return self.get_val("userestrict/head")

