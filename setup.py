from distutils.core import setup

from require import __version__


version_str = ".".join(str(n) for n in __version__)


setup(
    name = "django-require",
    version = version_str,
    license = "BSD",
    description = "A Django staticfiles post-processor for optimizing with RequireJS.",
    author = "Dave Hall",
    author_email = "dave@etianen.com",
    url = "https://github.com/etianen/django-require",
    download_url = "https://github.com/downloads/etianen/django-require/django-require-{0}.tar.gz".format(version_str),
    packages = [
        "require",
        "require.management",
        "require.management.commands",
        "require.templatetags",
        "require.tests",
    ],
    package_data = {
        "require": [
            "resources/*.jar",
            "resources/*.js",
        ],
        "require.tests": [
            "resources/*.js",
        ],
    },
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ],
)
