import posixpath

from require.settings import REQUIRE_BASE_URL


def resolve_require_url(name):
    return posixpath.normpath(posixpath.join(REQUIRE_BASE_URL, name))