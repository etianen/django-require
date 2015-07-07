from __future__ import absolute_import

from django import template

from django.contrib.staticfiles.storage import staticfiles_storage

from require.conf import settings as require_settings
from require.helpers import resolve_require_url, resolve_require_module, resolve_require_module_hash


register = template.Library()


@register.simple_tag
def require_module(module, mode=None):
    """
    Inserts a script tag to load the named module, which is relative to the REQUIRE_BASE_URL setting.
    
    If the module is configured in REQUIRE_STANDALONE_MODULES, and REQUIRE_DEBUG is False, then
    then the standalone built version of the module will be loaded instead, bypassing require.js
    for extra load performance.
    
    If your require.config uses shimed modules, set mode='shim'.  
    - If the module is configured in REQUIRE_COMMON_MODULE, and REQUIRE_DEBUG is False, then then the 
    common module will be loaded with requirejs embedded, bypassing an additional load of require.js 
    for extra load performance.
    - If the specified module does not match REQUIRE_COMMON_MODULE and REQUIRE_DEBUG is False a script
    tag will be inserted requireing the specified module.  If REQUIRE_DEBUG is True, a script tag will 
    be inserted requireing the common module with a nested require call of the specified module.
    """
    if not require_settings.REQUIRE_DEBUG:
        if module in require_settings.REQUIRE_STANDALONE_MODULES:
            string = u"""<script src="{module}"></script>""".format(
                module = staticfiles_storage.url(resolve_require_module(require_settings.REQUIRE_STANDALONE_MODULES[module]["out"])))
        elif module in require_settings.REQUIRE_COMMON_MODULE:
            # Load common (Assume requirejs is included with common)
            string = u"""<script src="{common}"></script>""".format(
                common = staticfiles_storage.url(resolve_require_module(require_settings.REQUIRE_COMMON_MODULE[module]["out"])))
        else:
            # Load additional modules (Assume that requirejs is accessible)
            string = u"""<script>require(['{module}']);</script>""".format(
                module = resolve_require_module_hash(module))
        return string

    elif require_settings.REQUIRE_COMMON_MODULE:
            common_keys = require_settings.REQUIRE_COMMON_MODULE.keys()
            common_module = common_keys[0]
            # The specified module is the common module
            if module in require_settings.REQUIRE_COMMON_MODULE:
                if mode == 'shim':
                    # Requirejs and shim common module
                    string = u"""<script src="{requirejs}"></script>""".format(
                        requirejs = staticfiles_storage.url(resolve_require_url(require_settings.REQUIRE_JS)))
                    string += u"""<script>require(['{common}']);</script>""".format(
                        common = staticfiles_storage.url(resolve_require_module(common_module)))
                else:
                    # Requirejs and data-main common module
                    string = u"""<script src="{requirejs}" data-main="{common}"></script>""".format(
                        requirejs = staticfiles_storage.url(resolve_require_url(require_settings.REQUIRE_JS)),
                        common = staticfiles_storage.url(resolve_require_module(common_module)))
            # The specified module is not the common module (assume common has already been loaded)
            elif mode == 'shim':
                # Require common and nest a require for the specified module
                string = u"""<script>require(['{common}'], function () {{""".format(
                    common = staticfiles_storage.url(resolve_require_module(common_module)))
                string += u"""require(['{module}']);""".format(
                    module = resolve_require_module_hash(module))
                string += u"""});</script>"""
            # Non shim mode template inheritance
            else:
                # Just require the specified module
                string = u"""<script>require(['{module}']);</script>""".format(
                    module = resolve_require_module_hash(module))

            return string

    return u"""<script src="{src}" data-main="{module}"></script>""".format(
        src = staticfiles_storage.url(resolve_require_url(require_settings.REQUIRE_JS)),
        module = staticfiles_storage.url(resolve_require_module(module)),
                )