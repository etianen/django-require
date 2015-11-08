from __future__ import absolute_import

from django import template
from django.contrib.staticfiles.storage import staticfiles_storage

from require.conf import settings as require_settings
from require.helpers import resolve_require_module, resolve_require_url

register = template.Library()


@register.simple_tag
def require_module(module):
    """
    Inserts a script tag to load the named module, which is relative to
    the REQUIRE_BASE_URL setting.

    If the module is configured in REQUIRE_STANDALONE_MODULES, and
    REQUIRE_DEBUG is False, then then the standalone built version of
    the module will be loaded instead, bypassing require.js for extra
    load performance.
    """
    if not require_settings.REQUIRE_DEBUG and \
            module in require_settings.REQUIRE_STANDALONE_MODULES:
        return '<script src="{module}"></script>'.format(
            module=staticfiles_storage.url(
                resolve_require_module(
                    require_settings.REQUIRE_STANDALONE_MODULES[
                        module]["out"])),
        )
    return '<script src="{src}" data-main="{module}"></script>'.format(
        src=staticfiles_storage.url(
            resolve_require_url(require_settings.REQUIRE_JS)),
        module=staticfiles_storage.url(resolve_require_module(module)),
    )
