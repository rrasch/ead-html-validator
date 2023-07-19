from bs4 import BeautifulSoup, NavigableString, Tag
from resultset import ResultSet
import logging
import os.path
import re
import util


class CompHTML:
    def __init__(self, c, cid):
        self.c = c
        self.id = cid
        self.cid = cid
        self.level, self.recursion = self._level()
        self.present_id = None

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
        return self.formatted_note_text("acqinfo")

    def acqinfo_heading(self):
        return self.formatted_note_heading("acqinfo")

    def altformavail(self):
        return self.formatted_note_text("altformavail")

    def altformavail_heading(self):
        return self.formatted_note_heading("altformavail")

    def appraisal(self):
        return self.formatted_note_text("appraisal")

    def appraisal_heading(self):
        return self.formatted_note_heading("appraisal")

    def arrangement(self):
        return self.formatted_note_long("arrangement")

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
            if c.has_attr("id"):
                cid = c["id"]
            else:
                cid = c.find(re.compile(r"^h\d$"), recursive=False)["id"]
            comps.append(CompHTML(c, cid))
        return comps

    def component_id_level(self):
        regex = re.compile(r"^level")
        first_c = self.c.find("div", class_=regex)
        if first_c is None:
            return []
        id_level = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            if c.has_attr("id"):
                cid = c["id"]
            else:
                cid = c.find(re.compile(r"^h\d$"), recursive=False)["id"]
            id_level.append((cid, util.parse_level(c)[0]))
        return id_level

    def container(self):
        wrapper = self.md_group("ead-container-wrapper")
        if not wrapper:
            return None
        return CompHTML.find_all(
            wrapper, class_="ead-container", ignore_space=False
        )

    def contents(self):
        return [text for text in self.c.stripped_strings]

    def control_access(self):
        return self.md_group("controlaccess")

    def control_group(self, field):
        ctrl_access = self.md_group("controlaccess")
        if not ctrl_access:
            return None
        ctrl_group = ctrl_access.find(
            "div", class_=f"controlaccess-{field}-group"
        )
        if ctrl_group is None:
            return None
        # return ctrl_group.div.get_text(strip=True)
        if ctrl_group.div:
            return CompHTML.find_all(ctrl_group, "div")
        else:
            return None

    def control_group_val(self, field):
        ctrl_access = self.control_access()
        if not ctrl_access:
            return None
        ctrl_group = ctrl_access.find(
            "div", class_=f"controlaccess-{field}-group"
        )
        if not ctrl_group:
            return None
        return CompHTML.find_all(ctrl_group, class_="controlaccess-value")

    def corpname(self):
        return self.control_group_val("corpname")

    def creator(self):
        origin = self.md_group("origination")
        if origin is None:
            return None
        return CompHTML.find_all(
            origin, "div", class_=re.compile(r"name$"), get_text=False
        )

    def custodhist(self):
        return self.formatted_note_text("custodhist")

    def custodhist_heading(self):
        return self.formatted_note_heading("custodhist")

    def _dao(self, dao_type=""):
        return self.c.find_all(
            "div",
            class_=re.compile(rf"^md-group dao-item {dao_type}"),
            recursive=False,
        )

    def dao(self, html_dir, roles):
        daos = self._dao()
        if not daos:
            return None

        dao_set = ResultSet(value_type=dict)
        for i, dao in enumerate(daos):
            dao_data = {}

            dao_data["role"] = [dao["class"].split()[2]]
            if dao_data["role"][0] not in roles:
                continue

            get_text = dao_data["role"][0] != "external-link"
            desc = CompHTML.find_all(
                dao, attrs={"data-ead-element": "daodesc"}, get_text=get_text
            )
            if desc:
                dao_data["desc"] = desc.values()

            links = []
            for a in dao.find_all(
                "a", class_=re.compile(r"^dao-link"), href=True
            ):
                link = a["href"]
                if link.startswith("/"):
                    link = self.permalink(link, html_dir) or link
                links.append(link)
            if links:
                dao_data["link"] = links

            dao_set.add(dao.name, {f"dao {i + 1}.": dao_data}, dao.sourceline)

        return dao_set if dao_set else None

    def dao_desc(self):
        daos = self._dao()
        if daos is None:
            return None
        descriptions = ResultSet()
        for dao in daos:
            for desc in dao.find_all(class_=re.compile(r"dao-description")):
                text = [
                    string
                    for string in desc.strings
                    if not re.match("https?://", string)
                ]
                # descriptions.add("".join(text).strip())
                text = util.clean_text("".join(text))
                descriptions.add(desc.name, text, desc.sourceline)
        # return list(descriptions) if descriptions else None
        return descriptions if descriptions else None

    # def dao_desc(self):
    #     return self.dao_title()

    def dao_link(self):
        # daos = self._dao("external-link")
        daos = self._dao()
        if daos is None:
            return None
        links = ResultSet()
        for dao in daos:
            # links.update({a["href"] for a in dao.find_all("a")})
            link = CompHTML.find_all(dao, "a", attrib="href")
            if link:
                links.append(link)
        # return sorted(list(links)) if links else None
        return links if links else None

    def dao_title(self):
        daos = self._dao()
        if daos is None:
            return None
        logging.debug(daos)
        titles = ResultSet()
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
                # titles.add("".join(text).strip())
                text = util.clean_text("".join(text))
                titles.add(title.name, text, title.sourceline)
        # return list(titles) if titles else None
        return titles if titles else None

    def dimensions(self):
        return self.physdesc("dimensions")

    def extent(self):
        return self.physdesc("extent")

    def famname(self):
        return self.control_group_val("famname")

    def fileplan(self):
        return self.formatted_note_text("fileplan")

    def fileplan_heading(self):
        return self.formatted_note_heading("fileplan")

    @staticmethod
    def find_all(
        root,
        *args,
        attrib=None,
        get_text=True,
        join_text=False,
        join_uniq=True,
        sep="",
        join_sep=" ",
        ignore_space=False,
        clean_txt=True,
        **kwargs,
    ):
        nodes = root.find_all(*args, **kwargs)
        if not nodes:
            return None

        total_text = ""
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
                text = ""
                for child in node:
                    if isinstance(child, Tag):
                        text += child.get_text()
                    elif isinstance(child, NavigableString):
                        text += child
                        break
            if clean_txt:
                text = util.clean_text(text or "")
            if not text:
                continue
            result.add(node.name, text, node.sourceline)

        if join_text and result:
            result = result.join(sep=join_sep, uniq=join_uniq)

        return result.rs_or_none()

    def formatted_note(self, field):
        return self.c.find_all(
            "div", class_=f"md-group formattednote {field}", recursive=False
        )

    def formatted_note_heading(self, field):
        notes = self.formatted_note(field)
        if not notes:
            return None
        heading = ResultSet()
        for note in notes:
            hdr = CompHTML.find_all(
                note,
                re.compile(r"^h\d$"),
                class_="formattednote-header",
                sep="",
            )
            if hdr:
                heading.append(hdr)
        return heading if heading else None

    def formatted_note_long(self, *args, **kwargs):
        notes = self.formatted_note_text(
            *args,
            sep=" ",
            ignore_space=True,
            **kwargs,
        )
        return notes.join(sep=" ") if notes else None

    def formatted_note_text(self, field, **kwargs):
        notes = self.formatted_note(field)
        if not notes:
            return None
        text = ResultSet()
        for note in notes:
            # search_root = note if note.p else note.div
            search_root = note.div if note.select(":scope > div > p") else note
            values = CompHTML.find_all(
                search_root, re.compile("^(div|p)$"), recursive=False, **kwargs
            )
            if values:
                text.append(values)
        return text if text else None

    def function(self):
        return self.control_group("function")

    def genreform(self):
        return self.control_group_val("genreform")

    def geogname(self):
        return self.control_group_val("geogname")

    def _id(self):
        return self.id

    def _lang_material(self, lang_type):
        type_num = {
            "language": 1,
            "langmaterial": 2,
        }
        lang_type_num = type_num[lang_type]
        lang_group = self.md_group("langmaterial")
        if lang_group is None:
            return None
        return CompHTML.find_all(
            lang_group,
            # class_=re.compile(rf"^langmaterial{lang_type_num}")
            class_=f"ead-{lang_type}"
        )

    def langmaterial(self):
        return self._lang_material("langmaterial")

    def language(self):
        return self._lang_material("language")

    def _level(self):
        if (
            self.c.name == "div"
            and self.c.has_attr("class")
            and self.c["class"].startswith("level")
        ):
            lvl, recursion = util.parse_level(self.c)
        else:
            lvl = None
            recursion = None
        return (lvl, recursion)

    def materialspec(self):
        return self.formatted_note_text("materialspec")

    def md_group(self, group_name):
        return self.c.find(
            "div", class_=f"md-group {group_name}", recursive=False
        )

    def name(self):
        pass

    def occupation(self):
        return self.control_group_val("occupation")

    def odd(self):
        return self.formatted_note_long("odd")

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

    def permalink(self, link, html_dir):
        dirparts = link.strip(os.sep).split(os.sep)
        partner = dirparts[0]
        eadid = dirparts[1]
        logging.trace(f"parter: {partner}")
        logging.trace(f"eadid: {eadid}")
        logging.trace(f"dirparts: {dirparts[2:]}")

        html_file = os.path.join(html_dir, *dirparts[2:], "index.html")
        logging.debug(f"permalink html file: {html_file}")
        if not os.path.isfile(html_file):
            return None
        soup = BeautifulSoup(open(html_file), "html.parser")
        link = soup.find(class_="dl-permalink")
        if not link:
            return None
        url = link.contents[1].strip()
        logging.debug(f"permalink for {link} is {url}")
        return url

    def persname(self):
        return self.control_group_val("persname")

    def physdesc(self, field):
        phys_desc = self.formatted_note("physdesc")
        if not phys_desc:
            return None
        result = ResultSet()
        for header in phys_desc[0].find_all(
            re.compile("h\d"), class_=re.compile(field)
        ):
            div = header.find_next_sibling("div")
            if not (div and div.contents):
                continue
            first_child = div.contents[0]
            istext = isinstance(first_child, NavigableString)
            if (
                istext and not first_child.strip() or not istext
            ) and div.select(":scope > span"):
                val = CompHTML.find_all(div, "span")
            else:
                val = CompHTML.resultset(div)
            if val:
                result.append(val)
        return result if result else None

    def physfacet(self):
        return self.physdesc("physfacet")

    def physloc(self):
        loc = self.formatted_note("physloc")
        if not loc:
            return None
        return CompHTML.find_all(loc[0], "span")

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

    @staticmethod
    def resultset(node, xpath=None, sep=""):
        return ResultSet(xpath=xpath).add(
            node.name, util.clean_text(node.get_text(sep)), node.sourceline
        )

    def separatedmaterial(self):
        return self.formatted_note_text("separatedmaterial")

    def separatedmaterial_heading(self):
        return self.formatted_note_heading("separatedmaterial")

    def scopecontent(self):
        return self.formatted_note_long("scopecontent")

    def scopecontent_heading(self):
        return self.formatted_note_heading("scopecontent")

    def sub_components(self):
        return self.components()

    def subject(self):
        return self.control_group_val("subject")

    def title(self):
        text = ""
        unit_title = self.c.find(
            re.compile("h\d"), class_="unittitle", recursive=False
        )
        for child in unit_title:
            if not (
                isinstance(child, Tag)
                and child.get("class") in ["dates", "delim"]
            ):
                # text += child.get_text()
                text += util.strings(child)
        text = util.clean_text(text)
        if text:
            return ResultSet().add(unit_title.name, text, unit_title.sourceline)
        else:
            return None

    def unitdate(self):
        unit_title = self.c.find(
            re.compile(r"^h\d$"), class_="unittitle", recursive=False
        )
        if not unit_title:
            return None
        dates = CompHTML.find_all(
            unit_title, "span", class_="dates", clean_txt=False
        )
        if dates:
            dates = dates.update_values(util.clean_date)
        return dates

    def unitid(self):
        odd = self.formatted_note("odd")
        if odd is None:
            return None
        # return odd.find("span", class_="ead-num").get_text()
        return CompHTML.find_all(odd, "span", class_="ead-num")

    def unittitle(self):
        return self.title()

    def userestrict(self):
        return self.formatted_note_text("userestrict")

    def userestrict_heading(self):
        return self.formatted_note_heading("userestrict")
