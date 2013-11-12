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
    packages = [
        "require",
        "require.management",
        "require.management.commands",
        "require.templatetags",
    ],
    package_data = {
        "require": [
            "resources/*.jar",
            "resources/*.js",
            "resources/tests/*.js",
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
