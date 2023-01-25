from bs4 import BeautifulSoup
from lxml import etree as ET
from resultset import ResultSet
from string import punctuation
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
        # self.soup = BeautifulSoup(open(html_file), "html.parser")
        self.soup = BeautifulSoup(
            open(html_file), "html.parser", multi_valued_attributes=None
        )
        self.dom = ET.HTML(str(self.soup))
        self.html_file = html_file
        self.main = self._main()

    def author(self):
        return self.get_group_div_text("author")

    def abstract(self):
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

    def c_count(self):
        return len(self.soup.find_all(class_=re.compile(r"^data-level")))

    def chronlist(self):
        items = ResultSet(value_type=dict)
        clist = self.soup.find("span", class_="ead-chronlist")
        if not clist:
            return None
        for item in clist.find_all("span", class_="ead-chronitem"):
            date = item.find("span", class_="ead-date").get_text()
            group = item.find("span", class_="ead-eventgrp")
            events = [
                event.get_text()
                for event in group.find_all("span", class_="ead-event")
            ]
            items.add(item.name, {date: events}, item.sourceline)
        return items

    def chronlist_heading(self):
        clist = self.soup.find("span", class_="ead-chronlist")
        if not clist:
            return None
        return self.find_all("span", class_="ead-head", root=clist)

    def class_values(self, class_regex):
        return self.find_all(class_=re.compile(class_regex), get_text=False)

    @staticmethod
    def clean_date(date):
        punc = ",;"
        return re.sub(r",\s*(bulk|inclusive)\s*$", "", date).strip(f" {punc}")

    def collection(self):
        return self.unittitle()

    def collection_unitid(self):
        return self.unitid()

    def _component(self):
        components = self.soup.find("section", class_="c-items")
        ids = []
        for c in components.find_all(
            "div", class_=re.compile(r"^level"), recursive=False
        ):
            ids.append(c["id"])
        return ids

    def component(self):
        regex = re.compile(r"^level")
        first_c = self.soup.find("div", class_=regex)
        if first_c is None:
            return []
        comps = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            cid = c["id"] if c.has_attr("id") else c.h1["id"]
            comps.append(comphtml.CompHTML(c, cid))
        return comps

    def component_id_level(self):
        regex = re.compile(r"^level")
        first_c = self.soup.find("div", class_=regex)
        if first_c is None:
            return []
        id_level = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            cid = c["id"] if c.has_attr("id") else c.h1["id"]
            id_level.append((cid, re.split(r"[- ]", c["class"])[1]))
        return id_level

    def contents(self):
        return [text for text in self.soup.stripped_strings]

    def control_access(self):
        return self.main.find(class_="md-group controlaccess")

    def control_access_group(self, field):
        ctrl_access = self.control_access()
        group = ctrl_access.find("div", class_=f"controlaccess-{field}-group")
        if not group:
            return None
        result = ResultSet()
        for div in group.find_all("div"):
            result.add(
                div.name, util.clean_text(div.get_text()), div.sourceline
            )
        return result

    def control_access_group_val(self, field):
        ctrl_access = self.control_access()
        group = ctrl_access.find("div", class_=f"controlaccess-{field}-group")
        if not group:
            return None
        result = ResultSet()
        for node in group.find_all(class_="controlaccess-value"):
            result.add(
                node.name, util.clean_text(node.get_text()), node.sourceline
            )
        return result

    def corpname(self):
        corpnames = ResultSet()
        for result in [
            self.control_access_group_val("corpname"),
            self.find_all(class_=re.compile(r"(ead-)?corpname$")),
        ]:
            print(f"result: {result}")
            if result:
                corpnames.append(result)
        return corpnames if corpnames else None

    def creation_date(self):
        creation = self.soup.find("div", class_="creation")
        return self.find_all(class_="ead-date", root=creation)

    # def creator(self):
    #     creators = []
    #     for node in self.soup.find_all(
    #         "div", class_=re.compile(r"(corp|fam|pers)name role-Donor")
    #     ):
    #         donor = util.clean_text(node.contents[0])
    #         creators.append(donor)
    #     return sorted(creators)

    def creator(self):
        origination = self.soup.find(
            class_=re.compile(r"^md-group origination")
        )
        return self.find_all(
            "div",
            class_=re.compile(r"^(corp|fam|pers)name"),
            root=origination,
            get_text=False,
        )

    def creators(self):
        return self.creator()

    def custodhist(self):
        return self.formatted_note("custodhist")

    def dao(self):
        pass

    def dimensions(self):
        return self.formatted_note("dimensions")

    def eadid(self):
        urls = self.url()
        if not urls:
            return None
        return urls.update_values(lambda url: url.rstrip("/").split("/")[-1])

    def eadnum(self):
        return self.find_all("span", class_="ead-num")

    def ead_class_values(self, class_name):
        return self.find_all(class_=f"ead-{class_name}", get_text=False)

    def editionstmt(self):
        return self.formatted_note("editionstmt")

    def extent(self):
        return self.formatted_note("extent")

    def famname(self):
        famnames = ResultSet()
        for result in [
            self.find_all("div", class_=re.compile("^famname"), get_text=False),
            self.control_access_group_val("famname"),
        ]:
            if result:
                famnames.append(result)
        return famnames if famnames else None

    def find_all(self, *args, root=None, attrib=None, get_text=True, **kwargs):
        if root is None:
            root = self.soup
        nodes = root.find_all(*args, **kwargs)
        if not nodes:
            return None
        find_expr = util.create_args_str(*args, **kwargs)
        result = ResultSet(xpath=find_expr)
        for node in nodes:
            if attrib:
                text = node[attrib]
            elif get_text:
                text = node.get_text()
            else:
                text = node.contents[0]
            text = util.clean_text(text)
            result.add(node.name, text, node.sourceline)
        return result

    def find_component(self, cid):
        node = self.soup.find(attrs={"id": cid})
        if node is not None:
            if node.name == "div":
                return comphtml.CompHTML(node, cid)
            elif node.name.startswith("h"):
                return comphtml.CompHTML(node.parent, cid)
            else:
                raise ValueError("Invalid tag for component")
        else:
            raise ComponentNotFoundError(
                f"Can't find {cid} in {self.html_file}"
            )

    def find_component_by_heading(self, head_id):
        head = self.soup.find(re.compile(r"^h\d$"), {"id": head_id})
        if head is not None:
            return comphtml.CompHTML(head.parent, head_id)
        else:
            raise ComponentNotFoundError(
                f"Can't find {head_id} in {self.html_file}"
            )

    def formatted_note(self, field):
        notes = self.soup.find_all(
            "div", class_=f"md-group formattednote {field}"
        )
        if not notes:
            return None
        result = ResultSet()
        for note in notes:
            values = self.find_all(
                re.compile("^(div|p)$"), root=note, recursive=False
            )
            if values:
                result.append(values)
        return result if result else None

    def function(self):
        return self.control_access_group("function")

    def genreform(self):
        return self.control_access_group("genreform")

    def geogname(self):
        return self.control_access_group("geogname")

    def get_group_div_text(self, group_name):
        group = self.soup.find("div", class_=f"md-group {group_name}")
        if group and group.div:
            return self.find_all("div", root=group)
        else:
            return None

    def heading(self):
        return self.unittitle()

    def langcode(self):
        lang_codes = ResultSet()
        for lang_result in self.language():
            pyc_lang = pycountry.languages.get(name=lang_result["value"])
            if pyc_lang:
                lang_codes.add(
                    lang_result["tag"], pyc_lang.alpha_3, lang_result["lineno"]
                )
        return lang_codes if lang_codes else None

    def language(self):
        return self.find_all(class_="ead-language")

    def _main(self):
        return self.soup.find("main")

    def material_type(self):
        return self.genreform()

    def md_group(self, group):
        groups = self.main.find_all(class_=f"md-group {group}", recursive=False)
        if not groups:
            return None
        text = ResultSet()
        for group in groups:
            result = self.find_all(re.compile(r"^(div)$"), root=group)
            if result:
                text.append(result)
        return text if text else None

    def name(self):
        return self.find_all(class_="ead-name")

    def names(self):
        all_names = ResultSet()

        corp_regex = r"^(ead-)?corpname( role-Donor)?$"
        corpname = self.find_all(
            lambda tag: not re.search(
                r"repository", tag.parent.parent.get("class") or ""
            )
            and (
                re.search(corp_regex, tag.get("class") or "")
                or re.search(corp_regex, tag.get("data-field") or "")
            ),
            get_text=False,
            root=self.soup.body,
        )
        if corpname:
            all_names.append(corpname)

        corpname = self.control_access_group_val("corpname")
        if corpname:
            all_names.append(corpname)

        pers_regex = r"^(ead-)?persname( role-Donor)?$"
        # for name in [self.famname(), self.class_values(pers_regex)]:
        for name in [self.famname(), self.persname()]:
            print(f"NAME {name}")
            if name:
                all_names.append(name)

        return all_names if all_names else None

    def note(self):
        return self.formatted_note("notestmt")

    def occupation(self):
        return self.control_access_group("occupation")

    def odd(self):
        return self.formatted_note("odd")

    def persname(self):
        all_persnames = ResultSet()
        pers_regex = r"^(ead-)?persname( role-Donor)?$"
        for persnames in [
            # self.ead_class_values("persname"),
            self.class_values(pers_regex),
            self.control_access_group_val("persname"),
        ]:
            if persnames:
                all_persnames.append(persnames)
        return all_persnames if all_persnames else None

    def physfacet(self):
        return self.formatted_note("physfacet")

    def phystech(self):
        return self.formatted_note("phystech")

    def place(self):
        return self.control_access_group("geogname")

    def processinfo(self):
        return self.formatted_note("processinfo")

    def prefercite(self):
        return self.formatted_note("prefercite")

    def relatedmaterial(self):
        return self.formatted_note("relatedmaterial")

    def repository(self):
        repo = self.soup.find("div", class_="md-group repository")
        if not repo:
            return None
        return self.find_all("div", root=repo)
        # return EADHTML.resultset(repo.div) if repo.div else None

    @staticmethod
    def resultset(node, xpath=None):
        if not node:
            raise ValueError("Must give a value for node.")
        return ResultSet(xpath=xpath).add(
            node.name, node.get_text(), node.sourceline
        )

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

    def sponsor(self):
        return self.md_group("sponsor")

    def subject(self):
        return self.control_access_group("subject")

    def subjects(self):
        subj_set = ResultSet()
        for field in ["subject", "function", "occupation"]:
            subjs = self.control_access_group(field)
            if subjs:
                subj_set.append(subjs)
        return subj_set if subj_set else None

    def subtitle(self):
        return self.find_all(re.compile(r"^h\d$"), class_="subtitle")

    def title(self):
        titles = self.find_all(class_="ead-title")
        addl_title = self.control_access_group_val("title")
        if addl_title:
            titles.append(addl_title)
        return titles

    def title_head(self):
        return EADHTML.resultset(self.soup.title)

    def unitdate(self):
        return self.get_group_div_text("unit_date")

    def unitdate_all(self):
        return self.unitdate().update_values(EADHTML.clean_date)

    def unitdate_bulk(self):
        return self.unitdate().grep(lambda date: "bulk" in date)

    def unitdate_inclusive(self):
        return self.unitdate().grep(lambda date: "inclusive" in date)

    def unitdate_not_type(self):
        return self.unitdate().grep(
            lambda date: all(
                dtype not in date for dtype in ["bulk", "inclusive"]
            )
        )

    def unittitle(self):
        # return self.soup.main.find(
        #     re.compile(r"^h\d$"), class_="page-title"
        # ).get_text()
        return EADHTML.resultset(self.soup.main.h1)

    def unitid(self):
        return self.get_group_div_text("unit_id")

    def url(self):
        return self.find_all("link", rel="canonical", attrib="href")

    def userestrict(self):
        return self.formatted_note("userestrict")
