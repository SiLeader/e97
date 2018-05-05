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

import typing
from datetime import datetime, timezone
import uuid

import pymongo


__client = pymongo.MongoClient(tz_aware=True)
__db = __client["e97"]
__col = __db["archive"]


ARCHIVE_ID = "id"
ARCHIVED_DATE = "date"
PAGE_DATA = "data"
PAGE_ID = "page_id"

"""
{
    "id": ARCHIVE_ID,
    "date": datetime,
    "data": {PAGE_DATA},
    "page_id": PAGE_ID
}
"""


def add(data: typing.Dict[str, typing.Any]):
    from models import pages

    date = datetime.now(timezone.utc)
    page_id = data[pages.PAGE_ID]
    __col.insert_one({
        ARCHIVE_ID: str(uuid.uuid4()),
        ARCHIVED_DATE: date,
        PAGE_DATA: data,
        PAGE_ID: page_id
    })


def get(aid: str) -> typing.Optional[typing.Dict[str, typing.Any]]:
    return __col.find_one({ARCHIVE_ID: aid}, {"_id": False})


def get_by_page(pid: str) -> typing.List[typing.Dict[str, typing.Any]]:
    return list(__col.find({PAGE_ID: pid}, {"_id": False}))


def remove(aid: typing.Union[str, typing.List[str]]):
    if isinstance(aid, str):
        __col.delete_one({ARCHIVE_ID: aid})
    else:
        __col.delete_many({"$or": aid})
