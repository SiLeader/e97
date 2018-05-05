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

import hashlib
import base64
import re

STRETCH_COUNT = 10000


def compute_hash(data):
    bytes_ = data.encode(encoding="utf-8")
    salt = [
        base64.b16encode(bytes_).decode(encoding="utf-8"),
        base64.b32encode(bytes_).decode(encoding="utf-8"),
        base64.b64encode(bytes_).decode(encoding="utf-8"),
        base64.b85encode(bytes_).decode(encoding="utf-8")
    ]

    def to_salt(d, s):
        return (d + s + d + s + d + s).encode(encoding="utf-8")

    for i in range(STRETCH_COUNT):
        s512 = hashlib.sha512()
        s512.update(to_salt(data, salt[i % 4]))
        data = s512.hexdigest()

    return "$1$" + data


def version(hash_):
    if hash_ is None:
        return None
    match = re.match("\$(\d+)\$.+", hash_)
    if not match:
        return None
    return match.group(1)
