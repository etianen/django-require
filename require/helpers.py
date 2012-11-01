import posixpath

from require.conf import settings as require_settings


def resolve_require_url(name):
    return posixpath.normpath(posixpath.join(require_settings.REQUIRE_BASE_URL, name))


def resolve_require_module(name):
    if not posixpath.splitext(name)[-1].lower() == ".js":
        name += ".js"
    return resolve_require_url(name)