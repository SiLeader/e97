#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
  Copyright 2018 SiLeader.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""


import string
import random
import datetime

import pytz

import pdfkit

from docutils import nodes
from docutils.core import publish_parts
from docutils.parsers.rst import Directive, directives

from flask import url_for


def random_string(length=64):
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])


def get_current_datetime():
    return datetime.datetime.now(tz=datetime.timezone.utc)


def get_datetime_with_timezone(time_string, format_string, tz):
    dt = datetime.datetime.strptime(time_string, format_string)
    dt_tz = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond,
                              tz)
    return dt_tz


def rest_to_html_all(data: str) -> str:
    return publish_parts(data, writer_name="html")["whole"]


def rest_to_html(data: str) -> str:
    return publish_parts(data, writer_name="html")["html_body"]


def datetime_local_as_datetime(dt: datetime.datetime, timezone):
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return pytz.timezone(timezone).localize(dt)
    return dt.astimezone(pytz.timezone(timezone))


def create_pdf(content: str):
    html = rest_to_html_all(content)
    return pdfkit.from_string(
        input=html,
        output_path=False,
        css="static/common.css",
        options={
            "encoding": "UTF-8",
            "page-size": "A4",
            'margin-top': '0in',
            'margin-right': '0in',
            'margin-bottom': '0in',
            'margin-left': '0in',
        }
    )


class RelatedDirective(Directive):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    def run(self):
        q = self.arguments[0]
        title = q
        refuri = url_for("contents_show", pid=q)
        self.options['refuri'] = refuri
        self.options['name'] = title
        ref_node = nodes.reference(**self.options)
        ref_node += nodes.Text(title)

        node = nodes.inline()
        node += ref_node
        return [node]


class NewPageDirective(Directive):
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}
    has_content = False

    def run(self):
        node = nodes.paragraph()
        node.attributes["classes"] = ["page-break"]
        return [node]


directives.register_directive("related", RelatedDirective)
directives.register_directive("page-break", NewPageDirective)
