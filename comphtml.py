from bs4 import BeautifulSoup, NavigableString, Tag
import inspect
import logging
import re
import util


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
        return self.formatted_note_heading("accruals")

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

    def component(self):
        regex = re.compile(r"^level")
        first_c = self.c.find("div", class_=regex)
        if first_c is None:
            return []
        comps = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            comps.append(CompHTML(c, c["id"]))
        return comps

    def component_id_level(self):
        regex = re.compile(r"^level")
        first_c = self.c.find("div", class_=regex)
        if first_c is None:
            return []
        id_level = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            id_level.append((c["id"], re.split(r"[- ]", c["class"])[1]))
        return id_level

    def contents(self):
        return [text for text in self.c.stripped_strings]

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

    def dao(self, dao_type=""):
        return self.c.find_all(
            "div", class_=re.compile(rf"^md-group dao-item {dao_type}")
        )

    def dao_desc(self):
        daos = self.dao()
        if daos is None:
            return None
        descriptions = set()
        for dao in daos:
            for desc in dao.find_all(class_=re.compile(r"dao-description")):
                text = [
                    string
                    for string in desc.strings
                    if not re.match("https?://", string)
                ]
                descriptions.add("".join(text).strip())
        return list(descriptions) if descriptions else None

    # def dao_desc(self):
    #     return self.dao_title()

    def dao_link(self):
        daos = self.dao("external-link")
        if daos is None:
            return None
        links = set()
        for dao in daos:
            links.update({a["href"] for a in dao.find_all("a")})
        return sorted(list(links)) if links else None

    def dao_title(self):
        daos = self.dao()
        if daos is None:
            return None
        logging.debug(daos)
        titles = set()
        for dao in daos:
            for title in dao.find_all(class_=re.compile(r"item-title")):
                # text = [
                #     child
                #     for child in title.contents
                #     if isinstance(child, NavigableString)
                # ]
                text = [
                    string
                    for string in title.strings
                    if not re.match("https?://", string)
                ]
                # titles.add("".join(text).strip().rsplit(":", 1)[0])
                # titles.add(util.strip_date("".join(text).strip()))
                titles.add("".join(text).strip())
        return list(titles) if titles else None

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
        ).get_text(" ", strip=True)

    def formatted_note_text(self, field, p=True):
        note = self.formatted_note(field)
        if note is None:
            return None
        text_node = note.div.p if p else note.div
        return util.clean_text(text_node.get_text(" ", strip=True))

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
        # return lang.span.get_text()
        for tag in ["span", "div"]:
            lang_child = getattr(lang, tag)
            if lang_child is not None:
                return lang_child.get_text()
        return None

    def level(self):
        if (
            self.c.name == "div"
            and self.c.has_attr("class")
            and self.c["class"].startswith("level")
        ):
            lvl = re.split("[- ]", self.c["class"])[1]
        else:
            lvl = None
        return lvl

    def name(self):
        pass

    def occupation(self):
        return self.control_group("occupation")

    def odd(self):
        return self.formatted_note_text("odd", p=False)

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
        return util.clean_text(sib.get_text())

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
        # return self.c.find(re.compile("h\d"), class_="unittitle").text
        text = ""
        unit_title = self.c.find(re.compile("h\d"), class_="unittitle")
        for child in unit_title:
            if not (
                isinstance(child, Tag)
                and child.get("class") in ["dates", "delim"]
            ):
                text += child.get_text()
        return text

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
