---
name: World
layout: layout-1
title: Test
---

{{ page.title }}
================

Hello, *{{ page.name }}*!

My URL is [{{ page.url }}]({{ page.url}}).

Global: {{ site.global_x }}.

{% include "include-1.html" %}
