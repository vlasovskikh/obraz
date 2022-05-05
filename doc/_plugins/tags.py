# -*- coding: utf-8 -*-

# Copyright (c) 2013-2022 Andrey Vlasovskikh
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

"""Tags plugin for Obraz.

This plugin generates separate pages for tags.

You can configure it via the `tags_plugin` section of `_config.yml`. The
default implicit configuration is:

    tags_plugin:
      pages:
        - url: /tags/{tag}.html
          layout: tag

`pages` is a list of tag pages, it is possible to generate multiple sets of
tag pages, e.g. HTML and RSS.

The following template variables are available inside a tag template:

* `tag`: tag name
* `posts`: list of tagged blog post objects provided by Obraz

Requirements:

* Obraz >= 0.9.3
"""

from __future__ import unicode_literals
from typing import TypedDict, cast
import obraz


class TagsPageInfo(TypedDict):
    url: str
    layout: str


class TagsConfig(TypedDict, total=False):
    pages: list[TagsPageInfo]


class TagsSite(obraz.Site, total=False):
    tags_plugin: TagsConfig


class TagPage(obraz.Page):
    tag: str
    posts: list[obraz.Post]


__version__ = "0.1"
default_page_info: TagsPageInfo = {
    "url": "/tags/{tag}.html",
    "layout": "tag",
}


@obraz.processor
def process_tags(site: obraz.Site) -> None:
    """Processing tags."""
    site = cast(TagsSite, site)
    pages = site.get("pages", [])
    settings = site.get("tags_plugin", {})
    for page_info in settings.get("pages", [default_page_info]):
        for tag, posts in site.get("tags", {}).items():
            page: TagPage = {
                "url": page_info["url"].format(tag=tag),
                "layout": page_info["layout"],
                "content": "",
                "tag": tag,
                "posts": posts,
            }
            pages.append(page)
