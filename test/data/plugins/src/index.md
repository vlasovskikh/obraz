---
---

This page is {{ page.size }} bytes long.

Capitals:

<ul>
{%- for capital, country in site.test1.capitals.items() %}
  <li>Capital of {{ country }} is {{ capital }}</li>
{%- endfor %}
</ul>
