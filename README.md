django-require
==============

**django-require** is a Django staticfiles post-processor for optimizing with [RequireJS][].

[RequireJS]: http://requirejs.org/


Features
--------

*   Optimize your static assets using the excellent r.js optimizer.
*   Compile standalone modules using the [almond.js][] shim.
*   Compatible with any Django staticfiles storage backend.

[almond.js]: https://github.com/jrburke/almond


Installation
---------------

1.  Checkout the latest django-require release and copy or symlink the `require` directory into your `PYTHONPATH`.
2.  Add `'require'` to your `INSTALLED_APPS` setting.
3.  Set your `STATICFILES_STORAGE` setting to `'require.storage.OptimizedStaticFilesStorage'` or `'require.storage.OptimizedCachedStaticFilesStorage'`.  


Available settings
------------------

Available settings, and their default values, are shown below. You should configure this to match the layout of your
project's static files. Please consult the [RequireJS][] documentation for more information about how to build javascript
using RequireJS.

```python
# The baseUrl to pass to the r.js optimizer.
REQUIRE_BASE_URL = "js"

# The name of a build profile to use for your project, relative to REQUIRE_BASE_URL.
# A sensible value would be 'app.build.js'. Leave blank to use the built-in default build profile.
REQUIRE_BUILD_PROFILE = None

# The name of the require.js script used by your project, relative to REQUIRE_BASE_URL.
REQUIRE_JS = "require.js"

# A dictionary of standalone modules to build with almond.js.
# See the section on Standalone Modules, below.
REQUIRE_STANDALONE_MODULES = {}

# Whether to run django-require in debug mode.
REQUIRE_DEBUG = settings.DEBUG

# A tuple of files to exclude from the compilation result of r.js.
REQUIRE_EXCLUDE = ("build.txt",)
```


Generating require.js
---------------------

As a shortcut to downloading a copy of require.js from the internet, you can simply run the `require_init` management
to copy a version of require.js into your `STATICFILES_DIRS`, at the location specified by your `REQUIRE_BASE_URL`
and `REQUIRE_JS` settings.

```
$ ./manage.py require_init
```


Generating build profiles
-------------------------

In almost all cases, you'll want to create a custom build profile for your project. To help you get started, django-require
can generate a default build profile into your `STATICFILES_DIRS`. Just set your `REQUIRE_BUILD_PROFILE` setting to a build profile name,
and run `require_init`. A good name for a build profile would be `'app.build.js'`.

Any standalone modules that your specify with a build profile will also have a default build profile generated when you run this
command.


Running javascript modules in templates
---------------------------------------

You can run javascript modules in templates by using the `{% require_module %}` template tag.

```html
<html>
    {% load require %}
    <head>
        {% require_module 'main' %}
    </head>
    <body></body>
</html>
```

This template fragment would then render to something like:

```html
<html>
    <head>
        <script src="/static/js/require.js" data-main="/static/js/main.js"></script>
    </head>
    <body></body>
</html>
```

If the `'main'` module was specified as a standalone module in your `REQUIRE_STANDALONE_MODULES` setting, and `REQUIRE_DEBUG`
is `False`, then the template fragement would instead render as:

This template fragment would then render to something like:

```html
<html>
    <head>
        <script src="/static/js/main-built.js"></script>
    </head>
    <body></body>
</html>
```


Building standalone modules
---------------------------

As a further optimization to your code, you can build your modules to run independently of require.js, which can often speed
up page load times. Standalone modules are built using the almond.js shim, so consult the [almond.js][] documentation
to make sure that it's safe to build your module in standalone mode.

To specify standalone modules, simply add them to your `REQUIRE_STANDALONE_MODULES` setting, as below:

```python
REQUIRE_STANDALONE_MODULES = {
    "main": {
        # Where to output the built module, relative to REQUIRE_BASE_URL.
        "out": "main-built.js",
        
        # Optional: A build profile used to build this standalone module.
        "build_profile": "main.build.js",
    }
}
```


Running the r.js optmizer
-------------------------

The r.js optimizer is run automatically whenever you call the `collectstatic` management command. The optimizer
is run as a post-processing step on your static files.

django-require provides two storage classes that are ready to use with the r.js optimizer:

*   `require.storage.OptimizedStaticFilesStorage` - A filesystem-based storage that runs the r.js optimizer.
*   `require.storage.OptimizedCachedStaticFilesStorage` - As above, but fingerprints all files with an MD5 hash of their contents for HTTP cache-busting.


Creating your own optimizing storage classes
--------------------------------------------

You can add r.js optmization to any django staticfiles storage class by using the `require.storage.OptimizedFilesMixin`. For example, to make an optimizing
storage that uploads to Amazon S3 using `S3BotoStorage` from [django-storages][]:

```python
from storages.backends.s3boto import S3BotoStorage
from require.storage import OptimizedFilesMixin

# S3 storage with r.js optimization.
class OptimizedS3BotoStorage(OptimizedFilesMixin, S3BotoStorage):
    pass

# S3 storage with r.js optimization and MD5 fingerprinting.
from django.contrib.staticfiles.storage import CachedFilesMixin
class OptimizedCachedS3BotoStorage(OptimizedFilesMixin, CachedFilesMixin, S3BotoStorage):
    pass
```

[django-storages]: http://django-storages.readthedocs.org/en/latest/



Support and announcements
-------------------------

Downloads and bug tracking can be found at the [main project website][].

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