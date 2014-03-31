from __future__ import unicode_literals

import posixpath
from django.utils.importlib import import_module

from require.conf import settings as require_settings
from django.contrib.staticfiles.storage import staticfiles_storage



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


def resolve_require_module_hash(module):
    module_hash_name = staticfiles_storage.url(resolve_require_module(module)).split("/")[-1].replace('.js', '')
    module_path = module.split("/")
    module_path[-1]=module_hash_name
    module_name = "/".join(module_path)
    return module_name
