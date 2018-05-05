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
import uuid
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor as Executor
from functools import reduce

import pymongo

import settings
from models import archive


__client = pymongo.MongoClient(tz_aware=True)
__db = __client["e97"]
__col = __db["pages"]


PAGE_ID = "id"
TITLE = "title"
CONTENT = "content"
UPDATE = "update"
CREATE = "create"
BY = "by"
DATE = "date"


"""
{
    "id": PAGE_ID,
    "title": TITLE,
    "content": reStructuredText,
    "update": {
        "by": USER_ID,
        "date": datetime
    },
    "create": {
        "by": USER_ID,
        "date": datetime
    }
}
"""


def add(title: str, content: str, author: str) -> typing.Optional[str]:
    page_id = str(uuid.uuid4()) if settings.SEPARATE_PAGE_TITLE_AND_ID else title
    if __col.count({PAGE_ID: page_id}) > 0:
        return None

    date = datetime.now(timezone.utc)

    __col.insert_one({
        PAGE_ID: page_id,
        TITLE: title,
        CONTENT: content,
        UPDATE: {
            BY: author,
            DATE: date
        },
        CREATE: {
            BY: author,
            DATE: date
        }
    })
    return page_id


def update(
        pid: str,
        author: str,
        title: typing.Optional[str]=None,
        content: typing.Optional[str]=None) -> typing.Optional[str]:

    data = __col.find_one({PAGE_ID: pid}, {"_id": False})
    if data is not None:
        if settings.SAVE_TO_ARCHIVE:
            archive.add(data)
    else:
        return None

    if not settings.SEPARATE_PAGE_TITLE_AND_ID:
        if title is not None and pid != title:
            __col.delete_one({PAGE_ID: pid})
            pid = title

    data[PAGE_ID] = pid
    if title is not None:
        data[TITLE] = title

    if content is not None:
        data[CONTENT] = content

    data[UPDATE] = {
        BY: author,
        DATE: datetime.now(timezone.utc)
    }

    __col.update_one({PAGE_ID: pid}, {"$set": data}, upsert=True)
    return pid


def get(pid: str) -> typing.Optional[typing.Dict[str, typing.Any]]:
    return __col.find_one({PAGE_ID: pid}, {"_id": False})


def get_all() -> typing.List[typing.Dict[str, typing.Any]]:
    return list(__col.find({}, {"_id": False}))


def get_all_as_index(is_sorted=True) -> typing.Dict[str, typing.List[typing.Dict[str, typing.Any]]]:
    data = get_all()
    results = {}
    for datum in data:
        key = datum[TITLE][:1]
        key = key.upper()
        if key not in results:
            results[key] = []
        results[key].append(datum)

    if is_sorted:
        res = sorted(results.items(), key=lambda x: x[0])
        results.clear()
        for k, v in res:
            results[k] = v

    return results


def get_latest(n_item=20) -> typing.List[typing.Dict[str, typing.Any]]:
    data = get_all()
    data.sort(key=lambda x: x[UPDATE][DATE])
    data.reverse()
    return data[:n_item]


def __and_search(
        executor: Executor,
        target: typing.List[typing.Dict[str, typing.Any]],
        and_query: typing.List[str]) -> typing.List[typing.Dict[str, typing.Any]]:
    and_query = [q.lower() for q in and_query]

    def __and_impl(data, query):
        title = data[TITLE].lower()
        point = reduce(lambda x, y: x + y, [title.count(q) for q in query]) * 2

        content = data[CONTENT].lower()
        point += reduce(lambda x, y: x + y, [content.count(q) for q in query])
        data["__point"] = point
        return data

    res = executor.map(lambda t: __and_impl(t, and_query), target)

    result = []
    for r in res:
        if r["__point"] > 0:
            result.append(r)

    return result


def __or_search(
        executor: Executor,
        target: typing.List[typing.Dict[str, typing.Any]],
        or_query: typing.List[str]) -> typing.List[typing.Dict[str, typing.Any]]:
    or_query = [q.lower() for q in or_query]

    def __or_impl(data, query):
        title = data[TITLE].lower()
        point = reduce(lambda x, y: x + y, [title.count(q) for q in query]) * 2

        content = data[CONTENT].lower()
        point += reduce(lambda x, y: x + y, [content.count(q) for q in query])
        data["__point"] += point
        return data

    res = executor.map(lambda t: __or_impl(t, or_query), target)

    return list(res)


def __not_search(
        executor: Executor,
        target: typing.List[typing.Dict[str, typing.Any]],
        not_query: typing.List[str]) -> typing.List[typing.Dict[str, typing.Any]]:
    not_query = [q.lower() for q in not_query]

    def __not_impl(data, query):
        title = data[TITLE].lower()
        point = reduce(lambda x, y: x + y, [title.count(q) for q in query]) * 2

        content = data[CONTENT].lower()
        point += reduce(lambda x, y: x + y, [content.count(q) for q in query])
        data["__point"] -= point
        return data

    res = executor.map(lambda t: __not_impl(t, not_query), target)

    result = []
    for r in res:
        if r["__point"] > 0:
            result.append(r)

    return result


def search(
        and_query: typing.Optional[typing.List[str]],
        or_query: typing.Optional[typing.List[str]],
        not_query: typing.Optional[typing.List[str]]) -> typing.List[typing.Dict[str, typing.Any]]:
    target = get_all()

    with Executor() as executor:
        if and_query is not None and len(and_query) > 0:
            target = __and_search(executor, target, and_query)
        if or_query is not None and len(or_query) > 0:
            target = __or_search(executor, target, or_query)
        if not_query is not None and len(not_query) > 0:
            target = __not_search(executor, target, not_query)

    target.sort(key=lambda x: x["__point"])
    return target
