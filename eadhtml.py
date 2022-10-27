from bs4 import BeautifulSoup
from subprocess import PIPE
import comphtml
import logging
import pycountry
import re
import shutil
import util


class ComponentNotFoundError(Exception):
    pass


class EADHTML:
    def __init__(self, html_file):
        logging.debug(f"html_file={html_file}")
        self.soup = BeautifulSoup(
            open(html_file), "html.parser", multi_valued_attributes=None
        )
        # self.soup = BeautifulSoup(open(html_file), "html.parser")
        self.html_file = html_file

    def author(self):
        results = self.soup.find_all("div", class_="md-group author")
        return results[0].div.get_text()

    def abstract(self):
        logging.debug(self.html_file)
        return self.formatted_note("abstract")

    def accessrestrict(self):
        return self.formatted_note("accessrestrict")

    def accruals(self):
        return self.formatted_note("accruals")

    def acqinfo(self):
        return self.formatted_note("acqinfo")

    def altformavail(self):
        return self.formatted_note("altformavail")

    def appraisal(self):
        return self.formatted_note("appraisal")

    def arrangement(self):
        return self.formatted_note("arrangement")

    def bibliography(self):
        return self.formatted_note("bibliography")

    def bioghist(self):
        return self.formatted_note("bioghist")

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

    def custodhist(self):
        return self.formatted_note("custodhist")

    def chronlist(self):
        items = {}
        clist = self.soup.find("span", class_="ead-chronlist")
        for item in clist.find_all("span", class_="ead-chronitem"):
            date = item.find("span", class_="ead-date").get_text()
            group = item.find("span", class_="ead-eventgrp")
            events = [
                event.get_text()
                for event in group.find_all("span", class_="ead-event")
            ]
            items[date] = events
        return items

    def chronlist_heading(self):
        return util.clean_text(
            self.soup.find("span", class_="ead-chronlist")
            .find("span", class_="ead-head")
            .get_text()
        )

    def collection(self):
        return self.unittitle()

    def collection_unitid(self):
        return self.unitid()

    def component(self):
        return "TODO"

    def control_access_group(self, field):
        group = self.soup.find("div", class_=f"controlaccess-{field}-group")
        return [div.get_text() for div in group.find_all("div")]

    def corpname(self):
        return self.control_access_group("corpname")

    def dao(self):
        pass

    def dimensions(self):
        return self.formatted_note("dimensions")

    def eadid(self):
        return self.url().rstrip("/").split("/")[-1]

    def eadnum(self):
        return self.soup.find("span", class_="ead-num").get_text()

    def editionstmt(self):
        return self.formatted_note("editionstmt")

    def extent(self):
        return self.formatted_note("extent")

    def famname(self):
        return list(
            self.soup.find(
                "div", class_=re.compile("^famname")
            ).stripped_strings
        )[0]

    def find_component(self, head_id):
        head = self.soup.find(re.compile(r"^h\d$"), {"id": head_id})
        if head is not None:
            return comphtml.CompHTML(head.parent, head_id)
        else:
            raise ComponentNotFoundError(
                f"Can't find {head_id} in {self.html_file}"
            )

    def formatted_note(self, field):
        note = self.soup.find("div", class_=f"md-group formattednote {field}")
        if note is None:
            return None
        # text = note.div.p.get_text()
        for tag in ["div", "p"]:
            note_child = getattr(note, tag)
            if note_child is not None:
                return note_child.get_text(strip=True)
        return None

    def function(self):
        return self.control_access_group("function")

    def genreform(self):
        return self.control_access_group("genreform")

    def geogname(self):
        return self.control_access_group("geogname")

    def heading(self):
        return self.unittitle()

    def langcode(self):
        lang = pycountry.languages.get(name=self.language())
        return lang.alpha_3

    def language(self):
        return self.soup.find("div", class_="langusage").span.text

    def material_type(self):
        return self.genreform()

    def name(self):
        return "TODO"

    def names(self):
        return "TODO"

    def note(self):
        return self.formatted_note("notestmt")

    def occupation(self):
        return self.control_access_group("occupation")

    def odd(self):
        return self.formatted_note("odd")

    def physfacet(self):
        return self.formatted_note("physfacet")

    def phystech(self):
        return self.formatted_note("phystech")

    def processinfo(self):
        return self.formatted_note("processinfo")

    def prefercite(self):
        return self.formatted_note("prefercite")

    def persname(self):
        return self.control_access_group("persname")

    def place(self):
        return self.control_access_group("geogname")

    def relatedmaterial(self):
        return self.formatted_note("relatedmaterial")

    def repository(self):
        return self.soup.find(
            "div", class_="md-group repository"
        ).div.get_text()

    def revisiondesc(self):
        return self.formatted_note("revisiondesc")

    def root(self):
        pass

    def scopecontent(self):
        return self.formatted_note("scopecontent")

    def separatedmaterial(self):
        return self.formatted_note("separatedmaterial")

    def series(self):
        pass

    def subject(self):
        return self.control_access_group("subject")

    def subjects(self):
        return self.subject()

    # def title(self):
    #     return list(
    #         {
    #             title.get_text()
    #             for title in self.soup.find_all(class_="ead-title")
    #         }
    #     )

    def title(self):
        title_str = self.soup.title.get_text(strip=True)
        return title_str

    def unitdate(self):
        return [
            date.get_text()
            for date in self.soup.find("div", "md-group unit_date").find_all(
                "div"
            )
        ]

    def unitdate_bulk(self):
        return list(filter(lambda date: "bulk" in date, self.unitdate()))

    def unitdate_end(self):
        return self.unitdate()[-1]

    def unitdate_inclusive(self):
        return list(filter(lambda date: "inclusive" in date, self.unitdate()))

    def unitdate_normal(self):
        return self.unitdate()

    def unitdate_start(self):
        return self.unitdate()[0]

    def unittitle(self):
        return self.soup.main.find(
            re.compile(r"^h\d$"), class_="page-title"
        ).get_text()

    def unitid(self):
        return self.soup.find("div", class_="md-group unit_id").div.get_text()

    def url(self):
        return self.soup.find("link", rel="canonical")["href"]

    def userestrict(self):
        return self.formatted_note("userestrict")
