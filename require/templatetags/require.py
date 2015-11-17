from __future__ import absolute_import

import os
from django import template
from django.contrib.staticfiles.storage import staticfiles_storage

from require.conf import settings as require_settings
from require.helpers import resolve_require_module, resolve_require_url

register = template.Library()


def _get_standalone_entry_filename(module, module_section):
    """
    Get the entry filename for a standalone module from the
    configuration.

    Use the config section name if there's no 'entry_file_name' key (the
    old behavior).
    """
    # If there's no entry_file_name, use the module name.
    entry_file_name = module_section.get('entry_file_name', module)
    if not require_settings.REQUIRE_DEBUG:
        entry_file_name = module_section.get('out')
    return entry_file_name


def _build_standalone_tag(module):
    """
    Generate a RequireJS script tag for a standalone module.

    If the config has a 'devel_tag' attribute set to 'separate_tag',
    generate a separate tag type.
    """
    module_section = require_settings.REQUIRE_STANDALONE_MODULES[module]
    relative_baseurl = module_section.get('relative_baseurl', '')
    entry_file_name = _get_standalone_entry_filename(module, module_section)
    relative_path = os.path.join(relative_baseurl, entry_file_name)
    module_url = staticfiles_storage.url(resolve_require_module(relative_path))
    if not require_settings.REQUIRE_DEBUG:
        # Production mode, output the compiled script tag
        return (
            '<script type="text/javascript" src="{0}">'
            '</script>').format(module_url)
    # Development mode generation below
    devel_tag = module_section.get('devel_tag', 'data_attr')
    require_url = staticfiles_storage.url(
        resolve_require_url(require_settings.REQUIRE_JS))
    if devel_tag == 'separate_tag':
        # Separate script tag mode
        return (
            '<script type="text/javascript" src="{0}"></script>'
            '<script type="text/javascript" src="{1}"></script>').format(
            require_url, module_url)
    # Data attribute mode (devel_tag == 'data_attr')
    return (
        '<script type="text/javascript" src="{0}" data-main="{1}">'
        '</script>').format(require_url, module_url)


@register.simple_tag
def require_module(module):
    """
    Inserts a script tag to load the named module, which is relative to
    the REQUIRE_BASE_URL setting.

    If the module is configured in REQUIRE_STANDALONE_MODULES, then the
    standalone built version of the module will be loaded instead,
    bypassing require.js for extra load performance.
    """

    if module in require_settings.REQUIRE_STANDALONE_MODULES:
        return _build_standalone_tag(module)

    # Non-standalone mode
    return (
        '<script type="text/javascript" src="{src}" data-main="{module}">'
        '</script>').format(
        src=staticfiles_storage.url(
            resolve_require_url(require_settings.REQUIRE_JS)),
        module=staticfiles_storage.url(resolve_require_module(module)),
    )
