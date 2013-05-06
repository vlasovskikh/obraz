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

* No command line options

    Obraz has no command line options (apart from `--help`) and it accepts only
    one required command line argument: the site source. The site destination
    is always `_site`. You can specify options only via configuration
    parameters in `_config.yml`.

* Permalink syntax

    Permalinks are specifed as follows:

        /foo/bar/{year}/{month}/{day}/{title}.html

    Variables `i_month` and `i_day`, as well as built-in permalink styles, are
    not available.

* Plugin system

    Obraz has an experimental [plugin system][5]. It may be changed
    significantly in the future releases. Please refer the [source code][6]
    for more info.


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

* Some config options

    The following `_config.yml` options are not supported: `source`,
    `destination`, `safe`, `timezone`, `future`, `lsi`, `limit_posts`.

* Textile formatting

    Textile markup language is not supported.


Not in Obraz
------------

* Jekyll-compatible plugin system

    The [plugin system][5] of Obraz will never be compatible with Jekyll
    (Python vs Ruby).

* Built-in web server

    Obraz comes with no built-in web server. There are many lightweight web
    servers available. For example, there is a web server in the Python standard
    library:

        $ cd /path/to/site
        $ python -m SimpleHTTPServer

* Syntax highlighting

    No syntax highlighting is built into Obraz. You can use a cool
    [highlight.js][3] library to highlight your code using only _two_ lines of
    JavaScript code.

* Blog migration tools

    Obraz doesn't contain any blog migration tools. Use the tools from Jekyll in
    order to migrate from popular blog hosting sites to Obraz.


Found an incompatible behaviour or want to request a new feature? Please post
your reports to the [bug tracker][4].


  [1]: http://jekyllrb.com/docs
  [2]: http://jinja.pocoo.org/docs/templates/
  [3]: http://softwaremaniacs.org/soft/highlight/en/
  [4]: https://bitbucket.org/vlasovskikh/obraz/issues
  [5]: /plugins.html
  [6]: https://bitbucket.org/vlasovskikh/obraz/src/master/obraz.py

