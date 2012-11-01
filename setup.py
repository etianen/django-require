from distutils.core import setup


setup(
    name = "django-require",
    version = "0.1.2",
    description = "A Django staticfiles post-processor for optimizing with require.js.",
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