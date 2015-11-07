from setuptools import setup

from require import __version__

version_str = '.'.join(str(n) for n in __version__)


setup(
    name='django-require',
    version=version_str,
    license='BSD',
    description=(
        'A Django staticfiles post-processor for optimizing with RequireJS.'),
    author='Dave Hall',
    author_email='dave@etianen.com',
    url='https://github.com/etianen/django-require',
    test_suite='tests',
    packages=[
        'require',
        'require.management',
        'require.management.commands',
        'require.templatetags',
    ],
    package_data={
        'require': [
            'resources/*.jar',
            'resources/*.js',
            'resources/tests/*.js',
        ],
    },
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: pypy',
        'Programming Language :: Python :: pypy3',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
