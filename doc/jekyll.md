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

* Template system

    Jekyll uses the Liquid templates system written in Ruby, but Obraz is
    written in Python and it cannot use Liquid. Obraz uses the Jinja2 templates
    system by default. Note, that you can change the template system via
    [plugins][5].

    Jinja2 tag syntax is very similar to Liquid, but its set of filters is
    quite different. The process of translation a Liquid template to Jinja2 is
    usually straightforward. See the [Jinja2 templates documentation][2] for
    details.

    Jekyll filters in Obraz: `markdownify`.

* Plugin system

    Obraz has its own [plugin system][5] incompatible with Jekyll.

* Permalink syntax

    Permalinks are specified using Python curly braces string formatting. For
    example:

        /foo/bar/{year}/{month}/{day}/{title}.html

    Variables `i_month` and `i_day`, as well as built-in permalink styles, are
    not available.


Not Implemented Yet
-------------------

* New site command

    The `new` command is not supported.

* Textile markup

    Textile markup language is not supported. Note, that you can register
    custom markup filters via [plugins][5].

* Some template data variables

    The following template data variables are not supported: `paginator`,
    `site.related_posts`, `site.categories`,  `page.excerpt`, `page.categories`.

* Some command-line flags

    The following command-line flags are not supported: `--safe`, `--config`,
    `--drafts`, `--future`, `--lsi`, `--limit_posts`.

* Some config options

    The following `_config.yml` options are not supported: `safe`, `timezone`,
    `future`, `lsi`, `limit_posts`.


Not in Obraz
------------

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
  [5]: {{ site.baseurl }}/plugins.html
  [6]: https://bitbucket.org/vlasovskikh/obraz/src/master/obraz.py

