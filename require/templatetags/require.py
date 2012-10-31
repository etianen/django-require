from __future__ import absolute_import

from django import template

from django.contrib.staticfiles.storage import staticfiles_storage

from require.settings import REQUIRE_JS
from require.helpers import resolve_require_url


register = template.Library()


@register.simple_tag
def require_module(data_main):
    return u"""<script src="{src}" data-main="{data_main}"></script>""".format(
        src = staticfiles_storage.url(resolve_require_url(REQUIRE_JS)),
        data_main = staticfiles_storage.url(data_main),
    )