from constants import LONGTEXT_XPATH
from lxml import etree as ET
from pprint import pformat, pprint
from resultset import ResultSet
from urllib import parse
from uuid import uuid4
import constants as cs
import logging
import re
import util


class Component:
    def __init__(self, c, parent=None):
        self.c = c
        self.parent = None
        self.ead_file = None
        if parent:
            self.parent = parent
            self.ead_file = parent.ead_file
        self.id = self._id()
        self.level = self._level()

    def accessrestrict(self):
        return self.get_text("accessrestrict/*[not(self::head)]")

    def accessrestrict_heading(self):
        return self.heading("accessrestrict")

    def accruals(self):
        return self.get_text("accruals/p")

    def accruals_heading(self):
        return self.get_text("accruals/head")

    def acqinfo(self):
        return self.get_text("acqinfo/p")

    def acqinfo_heading(self):
        return self.get_text("acqinfo/head")

    def altformavail(self):
        return self.get_text("altformavail/p")

    def altformavail_heading(self):
        return self.get_text("altformavail/head")

    def appraisal(self):
        return self.get_text("appraisal/p")

    def appraisal_heading(self):
        return self.get_text("appraisal/head")

    def arrangement(self):
        return self.get_text_long(f"arrangement/{LONGTEXT_XPATH}")

    def arrangement_heading(self):
        return self.get_text("arrangement/head")

    def bioghist(self):
        # return self.get_text("bioghist/*[self::p or self::list]")
        return self.get_text("bioghist/p")

    def bioghist_heading(self):
        return self.get_text("bioghist/head")

    def component(self):
        return self.sub_components()

    def container(self):
        containers = {}
        for container in self.c.xpath("did/container"):
            # data = {k: v.strip() for k, v in container.attrib.items()}
            data = dict(container.attrib)
            if "id" not in data:
                data["id"] = str(uuid4())
            data.update(
                {
                    "name": container.text.strip(),
                    "child": [],
                    "tag": container.tag,
                    "lineno": container.sourceline,
                }
            )
            if "parent" in data:
                containers[data["parent"]]["child"].append(data["id"])
            containers[data["id"]] = data

        if not containers:
            return None

        result = ResultSet()
        for cid in containers.keys():
            data = containers[cid]
            if "parent" in data:
                continue
            text = []
            self.format_container(cid, containers, text)
            if not text:
                continue
            label = re.sub(r"\s*\[.*?\]\s*", "", data["label"])
            text = ", ".join(text) + f" (Material Type: {label})"
            text = util.clean_text(text)
            result.add(data["tag"], text, data["lineno"])

        return result.rs_or_none()

    def corpname(self):
        return self.get_text("controlaccess/corpname")

    def creator(self):
        return self.get_text(
            "did/origination[@label='Creator' or @label='source']/"
            "*[substring(name(),"
            " string-length(name()) - string-length('name') + 1) = 'name']"
        )

    def custodhist(self):
        return self.get_text("custodhist/p")

    def custodhist_heading(self):
        return self.get_text("custodhist/head")

    def _dao(self, return_list=False):
        daos = self.c.xpath("did/*[self::dao or self::daogrp]")
        if daos:
            for dao in daos:
                logging.trace(Component._tostring(dao))
            return daos
        else:
            return None

    def dao(self, roles):
        # xpath_dao = "did/*[self::dao or self::daogrp]"
        xpath_dao = ["did/dao", "did/daogrp"]
        xpath_fields = {
            "role": "(.|.//*)/@role",
            "desc": "daodesc/p",
            "link": "(.|.//*)/@href",
        }

        daos = []
        for expr in xpath_dao:
            daos.extend(self.c.xpath(expr))
        if not daos:
            return None

        dao_set = ResultSet(xpath=xpath_dao, value_type=dict)
        for i, dao in enumerate(daos):
            dao_data = {}
            for field, expr in xpath_fields.items():
                result = util.xpath(dao, expr, all_text=True)
                if result:
                    dao_data[field] = list(map(str.strip, result.values()))
                    # dao_data[field] = [val.strip() for val in result.values()]

            missing_role = "role" not in dao_data or not dao_data["role"][0]
            if (
                missing_role
                and "link" in dao_data
                and not util.is_url(dao_data["link"][0])
            ):
                dao_data["role"] = ["non-url"]
                non_urls = dao_data.pop("link", None)
            elif missing_role:
                dao_data["role"] = ["external-link"]

            if dao_data["role"][0] not in roles:
                continue

            dao_data["desc"] = [";".join(dao_data["desc"])]

            if "link" in dao_data:
                dao_data["link"] = util.change_handle_scheme(*dao_data["link"])

            # put dict back in order
            dao_data = {
                field: dao_data[field]
                for field in xpath_fields.keys()
                if field in dao_data
            }

            dao_set.add(dao.tag, {f"dao {i + 1}.": dao_data}, dao.sourceline)

        return dao_set if dao_set else None

    def dao_desc(self):
        return self.get_text("did/*[self::dao or self::daogrp]/daodesc/p")

    def dao_link(self):
        links = ResultSet()
        href = "href"
        daos = self._dao()
        if not daos:
            return None
        for dao in daos:
            for link in dao.xpath("(.|.//*)[@*[local-name()='href']]"):
                url = link.get(href)
                host = parse.urlsplit(url).netloc
                if host == "hdl.handle.net":
                    target = util.resolve_handle(url)
                    logging.trace(f"dao link {url} resolves to {target}")

                links.add(link.tag, url, link.sourceline)
        return links if links else None

    def dao_title(self):
        title_attrib = "title"
        daos = self._dao()
        if daos:
            titles = {
                dao.sourceline: dao.get(title_attrib)
                for dao in daos
                if dao.get(title_attrib)
            }
            return util.sort_dict(titles) if titles else None
        else:
            return None

    def dimensions(self):
        return self.get_text_join("did/physdesc/dimensions")

    def extent(self):
        extent_xpath = "did/physdesc/extent"
        result = ResultSet(xpath=extent_xpath)
        for extent in self.c.xpath(extent_xpath):
            text = util.tag_text(extent)
            unit = extent.get("unit")
            if unit:
                text += " " + unit
            text = util.clean_text(text)
            if text:
                result.add(extent.tag, text, extent.sourceline)
        return result.rs_or_none()

    def famname(self):
        return self.get_text_join("controlaccess/famname")

    def fileplan(self):
        return self.get_text("fileplan/p")

    def fileplan_heading(self):
        return self.get_text("fileplan/head")

    def format_container(self, cid, containers, text):
        if containers[cid].get("type") and containers[cid].get("name"):
            text.append(f"{containers[cid]['type']}: {containers[cid]['name']}")
        elif containers[cid].get("name"):
            text.append(containers[cid]["name"])
        for child_id in containers[cid]["child"]:
            self.format_container(child_id, containers, text)

    def function(self):
        return self.get_text("controlaccess/function")

    def genreform(self):
        return self.get_text("controlaccess/genreform")

    def geogname(self):
        return self.get_text("controlaccess/geogname")

    def get_text(self, expr, **kwargs):
        return util.xpath(self.c, expr, all_text=True, **kwargs)

    def get_text_join(self, expr, **kwargs):
        return util.xpath(self.c, expr, all_text=True, join_text=True, **kwargs)

    def get_text_long(self, expr, **kwargs):
        return util.xpath(
            self.c,
            expr,
            all_text=True,
            join_text=True,
            sep=" ",
            join_sep=" ",
            ignore_space=True,
            **kwargs,
        )

    def heading(self, field):
        head = self.get_text(f"{field}/head")
        if head:
            return head
        field_exists = self.c.xpath(field)
        default = cs.DEFAULT_HEADINGS.get(field, None)
        if field_exists and default:
            return ResultSet().add("None", default, -1)
        else:
            None

    def _id(self):
        return self.c.attrib["id"]

    def langcode(self):
        return self.get_text("did/langmaterial/language/@langcode")

    def language(self):
        return self.get_text("did/langmaterial/language")

    def _level(self):
        return self.c.attrib["level"]

    def materialspec(self):
        return self.get_text("did/materialspec")

    def name(self):
        pass

    def occupation(self):
        return self.get_text("controlaccess/occupation")

    def odd(self):
        return self.get_text_long(f"odd/{LONGTEXT_XPATH}")

    def odd_heading(self):
        return self.get_text("odd/head")

    def originalsloc(self):
        return self.get_text("originalsloc/p")

    def originalsloc_heading(self):
        return self.get_text("originalsloc/head")

    def otherfindaid(self):
        return self.get_text("otherfindaid/p")

    def otherfindaid_heading(self):
        return self.get_text("otherfindaid/head")

    def persname(self):
        return self.get_text("controlaccess/persname")

    def physfacet(self):
        return self.get_text("did/physdesc/physfacet")

    def physloc(self):
        return self.get_text("did/physloc")

    def phystech(self):
        return self.get_text("phystech/p")

    def phystech_heading(self):
        return self.get_text("phystech/head")

    def prefercite(self):
        return self.get_text("prefercite/p")

    def prefercite_heading(self):
        return self.get_text("prefercite/head")

    def processinfo(self):
        return self.get_text("processinfo/p")

    def processinfo_heading(self):
        return self.get_text("processinfo/head")

    def relatedmaterial(self):
        return self.get_text("relatedmaterial/p")

    def relatedmaterial_heading(self):
        return self.get_text("relatedmaterial/head")

    def separatedmaterial(self):
        return self.get_text("separatedmaterial/p")

    def separatedmaterial_heading(self):
        return self.get_text("separatedmaterial/head")

    def scopecontent(self):
        return self.get_text_long(f"scopecontent/{LONGTEXT_XPATH}")

    def scopecontent_heading(self):
        return self.get_text("scopecontent/head")

    def sub_components(self):
        sub_comps = []
        for child in self.c:
            if child.tag == "c":
                sub_comps.append(Component(child, self))
        return sub_comps

    def subject(self):
        return self.get_text("controlaccess/subject")

    @staticmethod
    def _tostring(node):
        return ET.tostring(node, pretty_print=True).decode()

    def title(self):
        return self.unittitle()

    def unitdate(self):
        date_xpath = "did/unitdate[@datechar='creation']"
        unitdates = ResultSet(xpath=date_xpath)

        for date in self.c.xpath(date_xpath):
            val = date.text.strip()
            if val:
                val = util.clean_date(val)
                if "type" in date.attrib:
                    val += ", " + date.get("type")
            elif "normal" in date.attrib:
                val = date.get("normal")
                val = util.clean_date_normal(val)
                print(val)

            if val:
                unitdates.add(date.tag, val, date.sourceline)

        return unitdates.rs_or_none()

    def unitid(self):
        return self.get_text("did/unitid")

    def unittitle(self):
        return self.get_text_join("did/unittitle")

    def userestrict(self):
        return self.get_text("userestrict/p")

    def userestrict_heading(self):
        return self.get_text("userestrict/head")
