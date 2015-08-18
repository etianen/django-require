from __future__ import unicode_literals

import posixpath
try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module

from require.conf import settings as require_settings



def import_module_attr(module):
    module, _, cls = module.rpartition('.')
    module = import_module(module)
    attr = getattr(module, cls)
    return attr


def resolve_require_url(name):
    return posixpath.normpath(posixpath.join(require_settings.REQUIRE_BASE_URL, name))


def resolve_require_module(name):
    if not posixpath.splitext(name)[-1].lower() == ".js":
        name += ".js"
    return resolve_require_url(name)
