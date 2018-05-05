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
import getpass

import pymongo

from models import security


__client = pymongo.MongoClient(tz_aware=True)
__db = __client["e97"]
__col = __db["users"]


USER_ID = "id"
NAME = "name"
PASSWORD = "password"
LEVEL = "level"


LEVEL_WRITER = "writer"
LEVEL_VIEWER = "viewer"

"""
{
    "id": USER_ID,
    "name": NAME
    "password": HASHED_PASSWORD,
    "level": LEVEL
}
"""


def add(uid: str, name: str, pw: str, level: str) -> bool:
    if level not in [LEVEL_VIEWER, LEVEL_WRITER]:
        return False

    if security.version(pw) is None:
        pw = security.compute_hash(pw)

    __col.insert_one({
        USER_ID: uid,
        NAME: name,
        PASSWORD: pw,
        LEVEL: level
    })
    return True


def remove(uid: str):
    __col.delete_one({USER_ID: uid})


def get(uid: str) -> typing.Optional[typing.Dict[str, typing.Any]]:
    return __col.find_one({USER_ID: uid}, {"_id": False})


def update(uid: str, pw: typing.Optional[str]=None, level: typing.Optional[str]=None):
    if pw is None and level is None:
        return

    query = {}
    if pw is not None:
        query[PASSWORD] = pw if security.version(pw) is not None else security.compute_hash(pw)

    if level is not None:
        query[LEVEL] = level

    __col.update_one({USER_ID: uid}, {"$set": query})


def check(uid: str, pw: str) -> bool:
    if security.version(pw) is None:
        pw = security.compute_hash(pw)

    ui = get(uid)
    if ui is None:
        return False

    return ui[PASSWORD] == pw


def to_name(uid: str):
    ui = get(uid)
    if ui is None:
        return uid
    return ui[NAME]


if __name__ == '__main__':
    print("Add user to system")
    _uid = input("ID(E-mail) >>> ")
    _name = input("Name >>> ")
    while True:
        _password = getpass.getpass("Password >>> ")
        _confirm = getpass.getpass("Password(Confirm) >>> ")
        if _password == _confirm:
            break
        print("Password is different from Password(Confirm)")

    if add(_uid, _name, _password, LEVEL_WRITER):
        print("OK")
    else:
        print("NG")
