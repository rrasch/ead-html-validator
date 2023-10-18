from bs4 import BeautifulSoup, NavigableString, Tag
from ead_html_validator.comphtml import CompHTML
from ead_html_validator.resultset import ResultSet
from lxml import etree as ET
from pprint import pformat, pprint
from string import punctuation
from subprocess import PIPE
from typing import List, Tuple
import ead_html_validator.util as util
import logging
import re
import shutil


class ComponentNotFoundError(Exception):
    pass


class EADHTML:
    def __init__(self, html_file, parser="html5lib"):
        logging.debug(f"html_file={html_file}")
        logging.debug(f"html_parser={parser}")
        self.soup = BeautifulSoup(
            open(html_file), parser, multi_valued_attributes=None
        )
        self.dom = ET.HTML(str(self.soup))
        self.html_file = html_file
        self.main = self._main()

    def author(self) -> ResultSet:
        return self.get_group_div_text("author")

    def abstract(self) -> ResultSet:
        return self.formatted_note("abstract")

    def accessrestrict(self) -> ResultSet:
        return self.formatted_note("accessrestrict")

    def accruals(self) -> ResultSet:
        return self.formatted_note("accruals")

    def acqinfo(self) -> ResultSet:
        return self.formatted_note("acqinfo")

    def altformavail(self) -> ResultSet:
        return self.formatted_note("altformavail")

    def appraisal(self) -> ResultSet:
        return self.formatted_note("appraisal")

    def arrangement(self) -> ResultSet:
        return self.formatted_note("arrangement")

    def bibliography(self) -> ResultSet:
        return self.formatted_note("bibliography")

    def bioghist(self) -> ResultSet:
        return self.formatted_note_long("bioghist")

    def c_count(self) -> int:
        return len(self.soup.find_all(class_=re.compile(r"^data-level")))

    # XXX recursive?
    def chronlist(self) -> ResultSet:
        items = ResultSet(value_type=dict)
        for clist in self.main.find_all(class_="ead-chronlist"):
            for item in clist.find_all(
                class_=re.compile(r"ead-(chronitem|chronlist-body)")
            ):
                date = item.find(class_="ead-date").get_text(strip=True)
                events = [
                    util.clean_text(event.get_text())
                    for event in item.find_all("span", class_="ead-event")
                ]
                items.add(item.name, {date: events}, item.sourceline)
        return items.rs_or_none()

    def chronlist_heading(self) -> ResultSet:
        headings = ResultSet()
        for clist in self.main.find_all(class_="ead-chronlist"):
            values = self.find_all(class_=re.compile("head"), root=clist)
            if values:
                headings.append(values)
        return headings.rs_or_none()

    def class_values(
        self, class_regex, all_values=False, get_text=False
    ) -> ResultSet:
        return self.class_values_helper(
            re.compile(class_regex), all_values=all_values, get_text=get_text
        )

    def class_values_helper(
        self, class_expr, all_values=False, get_text=False
    ) -> ResultSet:
        result = ResultSet()
        for root in self.get_roots(all_values):
            values = self.find_all(
                EADHTML.is_parent_not_nav_link,
                class_=class_expr,
                root=root,
                get_text=get_text,
            )
            if values:
                result.append(values)
        return result.rs_or_none()

    @staticmethod
    def clean_date(date) -> str:
        punc = ",;"
        return util.clean_date(re.sub(r",\s*(bulk|inclusive)\s*$", "", date))

    def collection(self) -> ResultSet:
        return self.unittitle()

    def collection_unitid(self) -> ResultSet:
        return self.unitid()

    def _component(self) -> List[str]:
        components = self.soup.find("section", class_="c-items")
        ids = []
        for c in components.find_all(
            "div", class_=re.compile(r"^level"), recursive=False
        ):
            ids.append(c["id"])
        return ids

    def component(self) -> List[CompHTML]:
        regex = re.compile(r"^level")
        first_c = self.soup.find("div", class_=regex)
        if first_c is None:
            return []
        comps = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            cid = c["id"] if c.has_attr("id") else c.h1["id"]
            comp = CompHTML(c, cid)
            if comp.level == "dl-presentation":
                for present_comp in comp.component():
                    present_comp.present_id = cid
                    comps.append(present_comp)
            else:
                comps.append(comp)
        logging.trace(f"EADHTML components:")
        for comp in comps:
            logging.trace(f"({comp.level}, {comp.id})")
        return comps

    def component_id_level(self) -> List[Tuple[str, str]]:
        return [(comp.id, comp.level) for comp in self.component()]

    def contents(self) -> List[str]:
        return [text for text in self.soup.stripped_strings]

    def control_access(self) -> Tag:
        return self.main.find(class_="md-group controlaccess", recursive=False)

    def control_access_group(self, field) -> ResultSet:
        ctrl_access = self.control_access()
        if not ctrl_access:
            return None
        group = ctrl_access.find("div", class_=f"controlaccess-{field}-group")
        if not group:
            return None
        result = ResultSet()
        for div in group.find_all("div"):
            result.add(
                div.name, util.clean_text(div.get_text()), div.sourceline
            )
        return result if result else None

    def control_access_group_val(self, field, all_values=False) -> ResultSet:
        if all_values:
            return self.control_access_group_val_all(field)
        else:
            return self.control_access_group_val_top(field)

    def control_access_group_val_all(self, field) -> ResultSet:
        ctrl_values = ResultSet()
        for group in self.soup.find_all(class_=f"controlaccess-{field}-group"):
            values = self.find_all(root=group, class_="controlaccess-value")
            if values:
                ctrl_values.append(values)
        return ctrl_values if ctrl_values else None

    def control_access_group_val_top(self, field) -> ResultSet:
        ctrl_access = self.control_access()
        if not ctrl_access:
            return None
        group = ctrl_access.find("div", class_=f"controlaccess-{field}-group")
        if not group:
            return None
        return self.find_all(root=group, class_="controlaccess-value")

    def corpname(self) -> ResultSet:
        corpnames = ResultSet()
        for result in [
            self.control_access_group_val("corpname"),
            self.find_all(class_=re.compile(r"corpname( |$)"), get_text=False),
        ]:
            if result:
                corpnames.append(result)
        return corpnames if corpnames else None

    def creation_date(self) -> ResultSet:
        creation = self.soup.find("div", class_="creation")
        return self.find_all(class_="ead-date", root=creation)

    def creator(self) -> ResultSet:
        origination = self.soup.find(
            class_=re.compile(r"^md-group origination")
        )
        return self.find_all(
            "div",
            class_=re.compile(r"^(corp|fam|pers)name"),
            root=origination,
            get_text=False,
        )

    def creators(self) -> ResultSet:
        return self.creator()

    def custodhist(self) -> ResultSet:
        return self.formatted_note_long("custodhist")

    def dimensions(self) -> ResultSet:
        return self.formatted_note("dimensions")

    def eadid(self) -> ResultSet:
        urls = self.url()
        if not urls:
            return None
        return urls.update_values(lambda url: url.rstrip("/").split("/")[-1])

    def eadnum(self) -> ResultSet:
        return self.find_all("span", class_="ead-num")

    @staticmethod
    def is_parent_not_nav_link(tag) -> bool:
        return tag.parent.get("class", "") != "nav-link"

    def ead_class_values(
        self, class_name, all_values=False, get_text=True
    ) -> ResultSet:
        return self.class_values_helper(
            re.compile(rf"^ead-{class_name}($| )"),
            all_values=all_values,
            get_text=get_text,
        )

    def editionstmt(self) -> ResultSet:
        return self.formatted_note("editionstmt")

    def extent(self) -> ResultSet:
        return self.formatted_note("extent")

    def famname(self) -> ResultSet:
        famnames = ResultSet()
        for result in [
            self.find_all("div", class_=re.compile("^famname"), get_text=False),
            self.control_access_group_val("famname"),
        ]:
            if result:
                famnames.append(result)
        return famnames if famnames else None

    def fasb_version(self) -> str:
        return self.soup.find("meta", attrs={"name": "appversion"})["content"]

    def find_all(
        self,
        *args,
        root=None,
        attrib=None,
        get_text=True,
        join_text=False,
        sep="",
        join_sep="",
        join_unique=True,
        ignore_space=False,
        clean_txt=True,
        **kwargs,
    ) -> ResultSet:
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
                if ignore_space:
                    strings = []
                    for string in node.stripped_strings:
                        strings.append(string)
                    text = sep.join(strings)
                else:
                    text = node.get_text(sep)
            else:
                first_child = node.contents[0]
                if isinstance(first_child, NavigableString):
                    text = first_child
                else:
                    text = first_child.get_text()
            if clean_txt:
                text = util.clean_text(text or "")
            if not text:
                continue
            result.add(node.name, text, node.sourceline)

        if join_text and result:
            result = result.join(sep=join_sep, uniq=join_uniq)

        return result.rs_or_none()

    def find_component(self, cid) -> CompHTML:
        node = self.soup.find(attrs={"id": cid})
        if node is not None:
            if node.name == "div":
                return CompHTML(node, cid)
            elif node.name.startswith("h"):
                return CompHTML(node.parent, cid)
            else:
                raise ValueError("Invalid tag for component")
        else:
            raise ComponentNotFoundError(
                f"Can't find {cid} in {self.html_file}"
            )

    def find_component_by_heading(self, head_id) -> CompHTML:
        head = self.soup.find(re.compile(r"^h\d$"), {"id": head_id})
        if head is not None:
            return CompHTML(head.parent, head_id)
        else:
            raise ComponentNotFoundError(
                f"Can't find {head_id} in {self.html_file}"
            )

    def formatted_note(
        self, field, join_text=False, join_sep="", **kwargs
    ) -> ResultSet:
        notes = self.main.find_all(
            "div", class_=f"md-group formattednote {field}", recursive=False
        )
        if not notes:
            return None

        result = ResultSet()
        for note in notes:
            if note.select(":scope > div > p"):
                logging.debug("Setting search root to child div.")
                search_root = note.div
            else:
                search_root = note
            values = self.find_all(
                re.compile("^(div|p)$"),
                root=search_root,
                recursive=False,
                **kwargs,
            )
            if values:
                result.append(values)

        if not result:
            return None
        elif join_text:
            return result.join(sep=join_sep)
        else:
            return result

    def formatted_note_long(self, *args, **kwargs) -> ResultSet:
        notes = self.formatted_note(
            *args,
            sep=" ",
            ignore_space=True,
            **kwargs,
        )
        return notes.join(sep=" ") if notes else None

    def function(self) -> ResultSet:
        return self.control_access_group("function")

    def genreform(self) -> ResultSet:
        return self.get_field("genreform")

    def geogname(self) -> ResultSet:
        return self.get_field("geogname")

    def get_field(self, field, all_values=False) -> ResultSet:
        result = ResultSet()
        for value in [
            self.control_access_group_val(field, all_values=all_values),
            self.ead_class_values(field, all_values=all_values),
        ]:
            if value:
                result.append(value)
        return result if result else None

    # XXX use recursive
    def get_group_div_text(self, group_name, **kwargs) -> ResultSet:
        group = self.soup.find("div", class_=f"md-group {group_name}")
        if group and group.div:
            return self.find_all("div", root=group, **kwargs)
        else:
            return None

    def get_roots(self, all_values) -> List[Tag]:
        if all_values:
            roots = [self.main]
        else:
            roots = [
                child
                for child in self.main
                if isinstance(child, Tag) and not child.get("data-level")
            ]
        return roots

    def heading(self) -> ResultSet:
        return self.unittitle()

    def langcode(self) -> ResultSet:
        lang_codes = ResultSet()
        for lang_result in self.language():
            pyc_lang = pycountry.languages.get(name=lang_result["value"])
            if pyc_lang:
                lang_codes.add(
                    lang_result["tag"], pyc_lang.alpha_3, lang_result["lineno"]
                )
        return lang_codes if lang_codes else None

    def language(self) -> ResultSet:
        return self.find_all(class_="ead-language")

    def langusage(self) -> ResultSet:
        lang_usage = self.find_all(class_="langusage")
        if lang_usage:
            return lang_usage.update_values(
                lambda text: re.sub(r"^Language:\s+", "", text)
            )
        else:
            return None

    def _main(self) -> Tag:
        return self.soup.find("main")

    def materialspec(self) -> ResultSet:
        return self.formatted_note("materialspec")

    def material_type(self) -> ResultSet:
        return self.get_field("genreform", all_values=True)

    def md_group(self, group) -> ResultSet:
        groups = self.main.find_all(class_=f"md-group {group}", recursive=False)
        if not groups:
            return None
        text = ResultSet()
        for group in groups:
            result = self.find_all(re.compile(r"^(div)$"), root=group)
            if result:
                text.append(result)
        return text if text else None

    def name(self) -> ResultSet:
        return self.find_all(class_="ead-name")

    def names(self) -> ResultSet:
        all_names = ResultSet()

        corp_regex = r"corpname( |$)"
        corpname = self.find_all(
            lambda tag: not re.search(
                r"repository", tag.parent.parent.get("class", "")
            )
            and (
                re.search(corp_regex, tag.get("class", ""))
                or re.search(corp_regex, tag.get("data-field", ""))
            ),
            get_text=False,
            root=self.soup.body,
        )
        if corpname:
            all_names.append(corpname)

        corpname = self.control_access_group_val_all("corpname")
        if corpname:
            all_names.append(corpname)

        for name_type in ["famname", "persname"]:
            for names in [
                self.class_values(rf"{name_type}( |$)", all_values=True),
                self.control_access_group_val_all(name_type),
            ]:
                if names:
                    all_names.append(names)

        return all_names if all_names else None

    def note(self) -> ResultSet:
        return self.formatted_note("notestmt")

    def occupation(self) -> ResultSet:
        return self.get_field("occupation")

    def originalsloc(self) -> ResultSet:
        return self.formatted_note("originalsloc")

    def odd(self) -> ResultSet:
        return self.formatted_note("odd")

    def persname(self) -> ResultSet:
        all_persnames = ResultSet()
        pers_regex = r"persname( |$)"
        for persnames in [
            self.class_values(pers_regex),
            self.control_access_group_val("persname"),
        ]:
            if persnames:
                all_persnames.append(persnames)
        return all_persnames if all_persnames else None

    def physfacet(self) -> ResultSet:
        return self.formatted_note("physfacet")

    def phystech(self) -> ResultSet:
        return self.formatted_note("phystech")

    def place(self) -> ResultSet:
        return self.get_field("geogname", all_values=True)

    def processinfo(self) -> ResultSet:
        return self.formatted_note("processinfo")

    def prefercite(self) -> ResultSet:
        return self.formatted_note("prefercite")

    def relatedmaterial(self) -> ResultSet:
        return self.formatted_note("relatedmaterial")

    def repository(self) -> ResultSet:
        repo = self.soup.find("div", class_="md-group repository")
        if not repo:
            return None
        return self.find_all("div", root=repo)
        # return EADHTML.resultset(repo.div) if repo.div else None

    @staticmethod
    def resultset(node, xpath=None) -> ResultSet:
        if not node:
            raise ValueError("Must give a value for node.")
        return ResultSet(xpath=xpath).add(
            node.name, node.get_text(), node.sourceline
        )

    def revisiondesc(self) -> ResultSet:
        return self.formatted_note("revisiondesc")

    def root(self) -> None:
        pass

    def scopecontent(self) -> ResultSet:
        return self.formatted_note_long("scopecontent")

    def separatedmaterial(self) -> ResultSet:
        return self.formatted_note("separatedmaterial")

    def series(self) -> None:
        pass

    def _sponsor(self) -> ResultSet:
        return self.md_group("sponsor")

    def sponsor(self) -> ResultSet:
        return self.xpath("//main/div[@class='md-group sponsor']/div")

    def subject(self) -> ResultSet:
        return self.get_field("subject")

    def subjects(self) -> ResultSet:
        subj_set = ResultSet()
        for field in ["subject", "function", "occupation"]:
            for subjs in [
                self.ead_class_values(field),
                self.control_access_group_val(field),
            ]:
                if subjs:
                    subj_set.append(subjs)
        return subj_set if subj_set else None

    def subtitle(self) -> ResultSet:
        return self.find_all(re.compile(r"^h\d$"), class_="subtitle")

    def title(self) -> ResultSet:
        title_set = ResultSet()
        for titles in [
            self.get_field("title"),
            self.find_all(attrs={"data-field": "title"}),
        ]:
            if titles:
                title_set.append(titles)
        return title_set.rs_or_none()

    def title_head(self) -> ResultSet:
        return EADHTML.resultset(self.soup.title)

    def unitdate(self) -> ResultSet:
        return self.get_group_div_text("unit_date", clean_txt=False)

    def unitdate_all(self) -> ResultSet:
        dates = self.unitdate()
        if dates:
            dates = dates.update_values(util.clean_date)
            dates = dates.join(uniq=False, sep="")
            return dates
        else:
            return None

    def unitdate_bulk(self) -> ResultSet:
        return self.unitdate().grep(lambda date: "bulk" in date)

    def unitdate_inclusive(self) -> ResultSet:
        return self.unitdate().grep(lambda date: "inclusive" in date)

    def unitdate_not_type(self) -> ResultSet:
        return self.unitdate().grep(
            lambda date: all(
                dtype not in date for dtype in ["bulk", "inclusive"]
            )
        )

    def unittitle(self) -> ResultSet:
        return self.find_all(
            root=self.main, class_="page-title", recursive=False
        )

    def unitid(self) -> ResultSet:
        return self.get_group_div_text("unit_id")

    def url(self) -> ResultSet:
        return self.find_all("link", rel="canonical", attrib="href")

    def userestrict(self) -> ResultSet:
        return self.formatted_note("userestrict")

    def xpath(self, xpath_expr) -> ResultSet:
        return util.xpath(self.dom, xpath_expr, all_text=True)
