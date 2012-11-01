from __future__ import absolute_import

from django import template

from django.contrib.staticfiles.storage import staticfiles_storage

from require.settings import REQUIRE_JS, REQUIRE_STANDALONE_MODULES, REQUIRE_DEBUG
from require.helpers import resolve_require_url, resolve_require_module


register = template.Library()


@register.simple_tag
def require_module(module):
    if not REQUIRE_DEBUG and module in REQUIRE_STANDALONE_MODULES:
        return u"""<script src="{module}"></script>""".format(
            module = staticfiles_storage.url(resolve_require_module(REQUIRE_STANDALONE_MODULES[module]["out"])),
        )
    return u"""<script src="{src}" data-main="{module}"></script>""".format(
        src = staticfiles_storage.url(resolve_require_url(REQUIRE_JS)),
        module = staticfiles_storage.url(resolve_require_module(module)),
    )