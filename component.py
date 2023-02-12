from lxml import etree as ET
from pprint import pprint
from resultset import ResultSet
from urllib import parse
import constants as cs
import logging
import re
import util


class Component:
    def __init__(self, c, parent):
        self.c = c
        self.parent = parent
        self.ead_file = parent.ead_file
        self.id = self._id()
        self.level = self._level()

    def accessrestrict(self):
        return self.get_val("accessrestrict/p")

    def accessrestrict_heading(self):
        return self.get_text_join("accessrestrict/head")

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

    def bioghist(self):
        return self.get_val("bioghist/p", sep="")

    def bioghist_heading(self):
        return self.get_val("bioghist/head")

    def container(self):
        containers = ResultSet(value_type=dict)
        for container in self.c.xpath("did/container"):
            # container_data = {k: v.strip() for k, v in container.attrib.items()}
            container_data = dict(container.attrib)
            container_data["name"] = container.text.strip()
            containers.add(
                container.tag,
                {container.get("id"): container_data},
                container.sourceline,
            )

        if not containers:
            return None

        first_container = containers.first_value()
        return ResultSet().add(
            first_container["tag"],
            self.format_containers(containers),
            first_container["lineno"],
        )

    def corpname(self):
        return self.get_val("controlaccess/corpname")

    def creator(self):
        return self.get_val(
            "did/origination[@label='Creator']/*[substring(name(),"
            " string-length(name()) - string-length('name') + 1) = 'name']"
        )

    def custodhist(self):
        return self.get_val("custodhist/p")

    def custodhist_heading(self):
        return self.get_val("custodhist/head")

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
                result = util.xpath(dao, expr)
                if result:
                    dao_data[field] = result.values()

            # role defaults to "external-link" for missing or empty
            # role attribute
            if "role" not in dao_data or not dao_data["role"][0]:
                dao_data["role"] = ["external-link"]

            dao_data["desc"] = [";".join(dao_data["desc"])]

            if "link" in dao_data and dao_data["role"][0] not in roles:
                dao_data.pop("link")

            dao_set.add(dao.tag, {f"dao {i + 1}.": dao_data}, dao.sourceline)

        return dao_set if dao_set else None

    def dao_desc(self):
        return self.get_val("did/*[self::dao or self::daogrp]/daodesc/p")

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
        return self.get_text_join("did/physdesc/extent")

    def famname(self):
        return self.get_text_join("controlaccess/famname")

    def fileplan(self):
        return self.get_val("fileplan/p")

    def fileplan_heading(self):
        return self.get_val("fileplan/head")

    def format_containers(self, containers):
        text = set()
        for data in containers.values():
            cid = next(iter(data))
            text.add(f"{data[cid]['type']}: {data[cid]['name']}")
            if "parent" not in data[cid]:
                label = re.sub(r"\s*\[.*?\]\s*", "", data[cid]["label"])
        return ", ".join(text) + f" (Material Type: {label})"

    def function(self):
        return self.get_val("controlaccess/function")

    def genreform(self):
        return self.get_val("controlaccess/genreform")

    def geogname(self):
        return self.get_val("controlaccess/geogname")

    def get_text(self, expr, **kwargs):
        return util.xpath(self.c, expr, all_text=True, **kwargs)

    def get_text_join(self, expr, **kwargs):
        return util.xpath(self.c, expr, all_text=True, join_text=True, **kwargs)

    def get_val(self, xpath_expr, **kwargs):
        return util.xpath(self.c, xpath_expr, all_text=True, **kwargs)

    def _id(self):
        return self.c.attrib["id"]

    def langcode(self):
        return self.get_val("did/langmaterial/language/@langcode")

    def language(self):
        return self.get_text_join("did/langmaterial/language")

    def _level(self):
        return self.c.attrib["level"]

    def name(self):
        pass

    def occupation(self):
        return self.get_val("controlaccess/occupation")

    def odd(self):
        return self.get_text("odd/*[self::p or self::list]")

    def odd_heading(self):
        return self.get_text_join("odd/head")

    def originalsloc(self):
        return self.get_val("originalsloc/p")

    def originalsloc_heading(self):
        return self.get_val("originalsloc/head")

    def otherfindaid(self):
        return self.get_val("otherfindaid/p")

    def otherfindaid_heading(self):
        return self.get_val("otherfindaid/head")

    def persname(self):
        return self.get_val("controlaccess/persname")

    def physfacet(self):
        return self.get_val("did/physdesc/physfacet")

    def physloc(self):
        return self.get_text("did/physloc")

    def phystech(self):
        return self.get_val("phystech/p")

    def phystech_heading(self):
        return self.get_val("phystech/head")

    def prefercite(self):
        return self.get_val("prefercite/p")

    def prefercite_heading(self):
        return self.get_val("prefercite/head")

    def processinfo(self):
        return self.get_val("processinfo/p")

    def processinfo_heading(self):
        return self.get_val("processinfo/head")

    def relatedmaterial(self):
        return self.get_val("relatedmaterial/p")

    def relatedmaterial_heading(self):
        return self.get_val("relatedmaterial/head")

    def separatedmaterial(self):
        return self.get_text_join("separatedmaterial/p")

    def separatedmaterial_heading(self):
        return self.get_val("separatedmaterial/head")

    def scopecontent(self):
        return self.get_val("scopecontent/p")

    def scopecontent_heading(self):
        return self.get_val("scopecontent/head")

    def sub_components(self):
        sub_comps = []
        for child in self.c:
            if child.tag == "c":
                sub_comps.append(Component(child, self))
        return sub_comps

    def subject(self):
        return self.get_val("controlaccess/subject")

    @staticmethod
    def _tostring(node):
        return ET.tostring(node, pretty_print=True).decode()

    def title(self):
        return self.unittitle()

    def unitdate(self):
        return self.get_val("did/unitdate")

    def unitid(self):
        return self.get_val("did/unitid")

    def unittitle(self):
        return self.get_text_join("did/unittitle")

    def userestrict(self):
        return self.get_val("userestrict/p")

    def userestrict_heading(self):
        return self.get_val("userestrict/head")
