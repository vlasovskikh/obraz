# -*- coding: utf-8 -*-

# Copyright (c) 2014-2022 Andrey Vlasovskikh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""Less plugin for Obraz.

This plugin generates CSS files from Less files using `lessc`.

Configuration in `_config.yml`:

    lessc: /path/to/lessc

Requirements:

* Obraz == 0.9.x
* lessc (npm install -g less)
"""


from __future__ import unicode_literals
import os
import subprocess
from typing import cast
import obraz


class LessSite(obraz.Site, total=False):
    lessc: str
    less_files: list[obraz.File]


@obraz.processor
def process_less(site: obraz.Site) -> None:
    """Look for Less files."""
    site = cast(LessSite, site)
    files = site.get("files", [])
    less_files = site.setdefault("less_files", [])
    for file_ in files:
        if file_["path"].endswith(".less"):
            files.remove(file_)
            less_files.append(file_)
            name, _ = os.path.splitext(file_["url"])
            file_["url"] = name + ".css"


@obraz.generator
def generate_less(site: obraz.Site) -> None:
    """Generate Less files."""
    site = cast(LessSite, site)
    lessc = site.get("lessc")
    if not lessc:
        raise Exception("No 'lessc' path in site config")
    for file_ in site.get("less_files", []):
        src = os.path.join(site["source"], file_["path"])
        dst = os.path.join(site["destination"], obraz.url2path(file_["url"]))
        obraz.make_dirs(os.path.dirname(dst))
        subprocess.check_call([lessc, src, dst])
