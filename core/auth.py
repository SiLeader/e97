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


import datetime
import os
import hashlib

from flask import session

from core import util

_LIMIT = datetime.timedelta(hours=5)
_STR_FORMAT = '%Y-%m-%d %H:%M:%S'
_STRETCHING = 10000

_nonce = {}


def __hash(data):
    for _ in range(_STRETCHING):
        s512 = hashlib.sha512()
        s512.update(data)
        data = s512.hexdigest().encode('utf-8')
    return data.decode('utf-8')


def login(uid, tz_name):
    session['id'] = uid
    session['limit'] = (util.get_current_datetime() + _LIMIT).strftime(_STR_FORMAT)
    session['timezone'] = tz_name

    nonce = __hash(os.urandom(1024))
    session['nonce'] = nonce
    _nonce[uid] = nonce
    return True


def check():
    if session.get('id') is None or session.get('limit') is None:
        logout()
        return False

    uid = session.get('id')
    if session.get('nonce') != _nonce[uid]:
        return False

    dt = util.get_datetime_with_timezone(session['limit'], _STR_FORMAT, datetime.timezone.utc)
    current = util.get_current_datetime()

    if dt <= current:
        logout()
        return False

    return login(session['id'], session['timezone'])


def logout():
    if session.get('id') is not None:
        session.pop('id')
    if session.get('limit') is not None:
        session.pop('limit')
    if session.get('timezone') is not None:
        session.pop('timezone')
    return True


def get_id():
    if check():
        return session['id']
    return None


def to_local_datetime(value):
    value = util.datetime_local_as_datetime(value, session['timezone'])
    return value.strftime("%Y/%m/%d %H:%M:%S.%f")
