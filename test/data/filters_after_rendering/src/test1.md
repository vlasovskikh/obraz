---
name: "*World*"
---

Hello {{ page.name }}!

<ul>
  {% for post in site.posts %}
    <li>{{ post.content }}</li>
  {% endfor %}
</ul>
