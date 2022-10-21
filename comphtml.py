from bs4 import BeautifulSoup
import inspect
import logging
import re


class CompHTML:
    def __init__(self, c, id):
        self.c = c
        self.id_ = id

    def __str__(self):
        # return str(self.c)
        return self.c.prettify()

    def accessrestrict(self):
        return self.formatted_note_text("accessrestrict")

    def accessrestrict_heading(self):
        return self.formatted_note_heading("accessrestrict")

    def accruals(self):
        return self.formatted_note_text("accruals")

    def accruals_heading(self):
        return self.formatted_note_text("accruals")

    def acqinfo(self):
        field = inspect.currentframe().f_code.co_name
        return self.formatted_note_text(field)

    def acqinfo_heading(self):
        field = inspect.currentframe().f_code.co_name[: -len("_heading")]
        return self.formatted_note_heading(field)

    def altformavail(self):
        pass

    def altformavail_heading(self):
        pass

    def appraisal(self):
        return self.formatted_note_text("appraisal")

    def appraisal_heading(self):
        return self.formatted_note_heading("appraisal")

    def arrangement(self):
        return self.formatted_note_text("arrangement")

    def arrangement_heading(self):
        return self.formatted_note_heading("arrangement")

    def bioghist(self):
        return self.formatted_note_text("bioghist")

    def bioghist_heading(self):
        return self.formatted_note_heading("bioghist")

    def control_group(self, field):
        cgroup = self.c.find("div", class_=f"controlaccess-{field}-group")
        if cgroup is None:
            return None
        return cgroup.div.get_text(strip=True)

    def corpname(self):
        return self.control_group("corpname")

    def creator(self):
        origin = self.c.find("div", class_="md-group origination")
        if origin is None:
            return None
        return [
            name.get_text()
            for name in origin.find_all("div", class_=re.compile(r"name$"))
        ]

    def custodhist(self):
        return self.formatted_note_text("custodhist")

    def custodhist_heading(self):
        return self.formatted_note_heading("custodhist")

    def dao(self):
        return self.c.find("div", re.compile(r"^md-group dao-item"))

    def dao_desc(self):
        dao = self.dao()
        if dao is None:
            return None
        return self.dao().div.a.get_text(strip=True)

    def dao_link(self):
        dao = self.dao()
        if dao is None:
            return None
        return self.dao().div.a.get("href")

    def dao_title(self):
        pass

    def dimensions(self):
        return self.physdesc("dimensions")

    def extent(self):
        return self.physdesc("extent")

    def famname(self):
        return self.control_group("famname")

    def fileplan(self):
        return self.formatted_note_text("fileplan")

    def fileplan_heading(self):
        return self.formatted_note_heading("fileplan")

    def formatted_note(self, field):
        return self.c.find("div", class_=f"md-group formattednote {field}")

    def formatted_note_heading(self, field):
        note = self.formatted_note(field)
        if note is None:
            return None
        return note.find(
            re.compile(r"^h\d$"), class_="formattednote-header"
        ).get_text()

    def formatted_note_text(self, field):
        note = self.formatted_note(field)
        if note is None:
            return None
        return note.div.p.get_text()

    def function(self):
        return self.control_group("function")

    def genreform(self):
        return self.control_group("genreform")

    def geogname(self):
        return self.control_group("geogname")

    def id(self):
        return self.id_

    def langcode(self):
        pass

    def language(self):
        lang = self.c.find("div", class_="md-group langmaterial")
        if lang is None:
            return None
        return lang.span.get_text()

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

    def occupation(self):
        return self.control_group("occupation")

    def odd(self):
        return self.formatted_note_text("odd")

    def odd_heading(self):
        return self.formatted_note_heading("odd")

    def originalsloc(self):
        return self.formatted_note_text("originalsloc")

    def originalsloc_heading(self):
        return self.formatted_note_heading("originalsloc")

    def otherfindaid(self):
        return self.formatted_note_text("otherfindaid")

    def otherfindaid_heading(self):
        return self.formatted_note_heading("otherfindaid")

    def persname(self):
        pass

    def physdesc(self, field):
        phys_desc = self.c.find("div", class_=re.compile("physdesc"))
        if not phys_desc:
            return None
        header = phys_desc.find(re.compile("h\d"), class_=re.compile(field))
        sib = header.find_next_sibling("div")
        return sib.text

    def physfacet(self):
        return self.physdesc("physfacet")

    def physloc(self):
        loc = self.formatted_note("physloc")
        if loc is None:
            return None
        return "".join([span.get_text() for span in loc.find_all("span")])

    def physloc_heading(self):
        return self.formatted_note_heading("physloc")

    def phystech(self):
        return self.formatted_note_text("phystech")

    def phystech_heading(self):
        return self.formatted_note_heading("phystech")

    def prefercite(self):
        return self.formatted_note_text("prefercite")

    def prefercite_heading(self):
        return self.formatted_note_heading("prefercite")

    def processinfo(self):
        return self.formatted_note_text("processinfo")

    def processinfo_heading(self):
        return self.formatted_note_heading("processinfo")

    def relatedmaterial(self):
        return self.formatted_note_text("relatedmaterial")

    def relatedmaterial_heading(self):
        return self.formatted_note_heading("relatedmaterial")

    def separatedmaterial(self):
        return self.formatted_note_text("separatedmaterial")

    def separatedmaterial_heading(self):
        return self.formatted_note_heading("separatedmaterial")

    def scopecontent(self):
        return self.formatted_note_text("scopecontent")

    def scopecontent_heading(self):
        return self.formatted_note_heading("scopecontent")

    def sub_components(self):
        pass

    def subject(self):
        return self.control_group("subject")

    def title(self):
        return self.c.find(re.compile("h\d"), class_="unittitle").text

    def unitdate(self):
        date = self.c.find(re.compile(r"^h\d$"), class_="unittitle").find(
            "span", class_="dates"
        )
        if date is None:
            return None
        return date.get_text()

    def unitid(self):
        odd = self.formatted_note("odd")
        if odd is None:
            return None
        return odd.find("span", class_="ead-num").get_text()

    def unittitle(self):
        return self.title()

    def userestrict(self):
        return self.formatted_note_text("userestrict")

    def userestrict_heading(self):
        return self.formatted_note_heading("userestrict")
