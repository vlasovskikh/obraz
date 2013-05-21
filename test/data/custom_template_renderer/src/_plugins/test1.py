import obraz


@obraz.template_renderer
def string_fmt_render(string, context, site):
    return string.format(**context)
