django-reversion
================

**django-require** is a Django staticfiles post-processor for optimizing with [RequireJS][].

[RequireJS]: http://requirejs.org/


Features
--------

*   Optimize your static assets using the excellent r.js optimizer.
*   Compile standalone modules using the [almond.js][] AMD shim.
*   Compatible with any Django staticfiles storage backend.

[almond.js]: https://github.com/jrburke/almond


Getting started
---------------

1.  Checkout the latest django-require release and copy or symlink the `require` directory into your `PYTHONPATH`.
2.  Add `'require'` to your `INSTALLED_APPS` setting.


Available settings
------------------

*   `REQUIRE_BASE_URL` - The baseUrl to pass to the r.js optimizer. Defaults to `'js'`.
*   `REQUIRE_BUILD_PROFILE` - The name of a build profile to use for your project, relative to `REQUIRE_BASE_URL`. Defaults to `None`. A sensible value would be `'app.build.js'`.
*   `REQUIRE_JS` - The name of the require.js script used by your project, relative to `REQUIRE_BASE_URL`. Defaults to `'require.js'`.
*   `REQUIRE_STANDALONE_MODULES` - A dictionary of standalone modules to build with [almond.js][]. Defaults to `{}`. Please see the Standalone Module section above.
*   `REQUIRE_DEBUG` - Whether to run django-require in debug mode. Defaults to `settings.DEBUG`.
*   `REQUIRE_EXCLUDE` - A tuple of files to exclude from the compilation result of r.js. Defaults to `('build.txt',)`. 


Support and announcements
-------------------------

Legacy downloads and bug reporting can be found at the [main project website][].

[main project website]: http://github.com/etianen/django-require
    "django-require on GitHub"

You can keep up to date with the latest announcements by joining the
[django-require discussion group][].

[django-require discussion group]: http://groups.google.com/group/django-require
    "django-require Google Group"

    
More information
----------------

The django-require project was developed by Dave Hall. You can get the code
from the [django-require project site][].

[django-require project site]: http://github.com/etianen/django-require
    "django-require on GitHub"
    
Dave Hall is a freelance web developer, based in Cambridge, UK. You can usually
find him on the Internet in a number of different places:

*   [Website](http://www.etianen.com/ "Dave Hall's homepage")
*   [Twitter](http://twitter.com/etianen "Dave Hall on Twitter")
*   [Google Profile](http://www.google.com/profiles/david.etianen "Dave Hall's Google profile")