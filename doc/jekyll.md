---
layout: default
title: Compatibility with Jekyll
---

{{ page.title }}
================

Obraz is mostly compatible with Jekyll. Since most parts of the [Jekyll
documentation][1] are valid for Obraz too, Obraz doesn't have its own
documentation.

However, there are several differences you should be aware of.

Different
---------

* Jinja2 template system

    Jekyll uses the Liquid templates system written in Ruby, but Obraz is
    written in Python and it cannot use Liquid. Obraz uses the Jinja2 templates
    system instead. Its tag syntax is very similar to Liquid, but its set of
    filters is quite different. The process of translation a Liquid template to
    Jinja2 is usually straightforward. See the [Jinja2 templates
    documentation][2] for details.

    Jekyll filters in Obraz: `markdownify`.

* Permalink syntax

    Permalinks are specifed as follows:

        /foo/bar/{year}/{month}/{day}/{title}.html

    Variables `i_month` and `i_day`, as well as built-in permalink styles, are
    not available.

* Plugin system

    Obraz has its own [plugin system][5] incompatible with Jekyll.


Not Implemented Yet
-------------------

* Categories of posts

    Categories of posts in template data (`site.categories`) and in permalinks
    are not supported.

* Posts paginator

    The posts paginator object in template data (`paginator`) is not supported.

* Related posts

    Related posts in template data (`site.related_posts`) are not supported.

* Page excerpt

    Page excerpt in template data (`page.excerpt`) is not supported.

* Page path

    The path to the raw page in template data (`page.path`) is not supported.

* New site command

    The `new` command is not supported.

* Some command-line flags

    The following command-line flags are not supported: `--safe`, `--watch`,
    `--config`, `--drafts`, `--future`, `--lsi`, `--limit_posts`.

* Some config options

    The following `_config.yml` options are not supported: `safe`, `timezone`,
    `future`, `lsi`, `limit_posts`.

* Textile formatting

    Textile markup language is not supported.


Not in Obraz
------------

* Jekyll-compatible plugin system

    The [plugin system][5] of Obraz will never be compatible with Jekyll
    (Python vs Ruby).

* Syntax highlighting

    No syntax highlighting is built into Obraz. You can use a cool
    [highlight.js][3] library to highlight your code using only _two_ lines of
    JavaScript code.

* Blog migration tools and `import` command

    Obraz doesn't contain any blog migration tools. Use the tools from Jekyll in
    order to migrate from popular blog hosting sites to Obraz.


Found an incompatible behaviour or want to request a new feature? Please post
your reports to the [bug tracker][4].


  [1]: http://jekyllrb.com/docs/home/
  [2]: http://jinja.pocoo.org/docs/templates/
  [3]: http://softwaremaniacs.org/soft/highlight/en/
  [4]: https://bitbucket.org/vlasovskikh/obraz/issues
  [5]: /plugins.html
  [6]: https://bitbucket.org/vlasovskikh/obraz/src/master/obraz.py

