from __future__ import unicode_literals

import os.path
import shutil
import subprocess
import tempfile
import unittest

import mock
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ImproperlyConfigured
from django.core.management import base, call_command
from django.test import TestCase
from django.test.utils import override_settings

from require.conf import settings as require_settings
from require.environments import AutoEnvironment, Environment
from require.storage import (
    OptimizationError, OptimizedFilesMixin, TemporaryCompileEnvironment)
from require.templatetags.require import require_module

WORKING_DIR = tempfile.mkdtemp()
WORKING_DIR2 = tempfile.mkdtemp()
OUTPUT_DIR = tempfile.mkdtemp()


class WorkingDirMixin(object):

    def tearDown(self):
        for working_dir in (WORKING_DIR, WORKING_DIR2, OUTPUT_DIR):
            for name in os.listdir(working_dir):
                path = os.path.join(working_dir, name)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            assert len(os.listdir(working_dir)) == 0


class RequireInitTest(WorkingDirMixin, TestCase):

    @override_settings(
        STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_JS='require.js')
    def test_copy_require(self):
        call_command('require_init', verbosity=0)
        self.assertTrue(os.path.exists(
            os.path.join(
                WORKING_DIR, require_settings.REQUIRE_BASE_URL,
                'require.js')))

    @override_settings(
        STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_JS='require.js')
    def test_copy_require_more_verbosity(self):
        call_command('require_init', verbosity=1)
        self.assertTrue(os.path.exists(
            os.path.join(
                WORKING_DIR, require_settings.REQUIRE_BASE_URL,
                'require.js')))

    @override_settings(
        STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_JS='require.js')
    @mock.patch('django.core.management.base.OutputWrapper.write')
    def test_copy_require_no_overwrite_mode(self, mock_stdout_write):
        """
        Init the module while not overwriting an existing asset.
        """
        os.mkdir(os.path.join(
            WORKING_DIR, require_settings.REQUIRE_BASE_URL))
        with open(os.path.join(
                WORKING_DIR, require_settings.REQUIRE_BASE_URL,
                'require.js'), 'w') as fp:
            fp.write('foo')
        call_command('require_init', verbosity=1)
        self.assertTrue(os.path.exists(
            os.path.join(
                WORKING_DIR, require_settings.REQUIRE_BASE_URL,
                'require.js')))
        self.assertEqual(mock_stdout_write.call_count, 1)
        self.assertRegexpMatches(
            mock_stdout_write.call_args[0][0],
            r'.*require.js already exists, skipping\.\n$')

    @override_settings(
        STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_JS='require.js')
    def test_more_working_dirs(self):
        """
        Test when more working dirs are passed, the latter is used.
        """
        call_command(
            'require_init', verbosity=0, dir=(WORKING_DIR, WORKING_DIR2))
        self.assertTrue(os.path.exists(
            os.path.join(
                WORKING_DIR2, require_settings.REQUIRE_BASE_URL,
                'require.js')))

    @override_settings(
        STATICFILES_DIRS=(), REQUIRE_JS='require.js')
    def test_empty_static_files(self):
        with self.assertRaisesMessage(
                base.CommandError,
                'settings.STATICFILES_DIRS is empty, and no --dir '
                'option specified'):
            call_command('require_init', verbosity=0)

    @override_settings(
        STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_JS='../require.js')
    def test_copy_require_relative(self):
        call_command('require_init', verbosity=0)
        self.assertTrue(os.path.exists(os.path.abspath(os.path.join(
            WORKING_DIR, require_settings.REQUIRE_BASE_URL, '..',
            'require.js'))))

    @override_settings(
        STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_BUILD_PROFILE='app.build.js')
    def test_copy_build_profile(self):
        call_command('require_init', verbosity=0)
        self.assertTrue(os.path.exists(
            os.path.join(
                WORKING_DIR, require_settings.REQUIRE_BASE_URL,
                'app.build.js')))

    @override_settings(
        STATICFILES_DIRS=(WORKING_DIR,),
        REQUIRE_STANDALONE_MODULES={
            'main': {'build_profile': 'module.build.js'}})
    def test_copy_standalone_profile(self):
        call_command('require_init', verbosity=0)
        self.assertTrue(os.path.exists(os.path.join(
            WORKING_DIR, require_settings.REQUIRE_BASE_URL,
            'module.build.js')))

    @override_settings(REQUIRE_JS='require.js')
    def test_copy_require_custom_dir(self):
        call_command('require_init', dir=WORKING_DIR, verbosity=0)
        self.assertTrue(os.path.exists(
            os.path.join(
                WORKING_DIR, require_settings.REQUIRE_BASE_URL, 'require.js')))


@override_settings(REQUIRE_JS='require.js', REQUIRE_BASE_URL='js')
class RequireModuleTest(TestCase):

    @override_settings(REQUIRE_STANDALONE_MODULES={})
    def test_require_module(self):
        self.assertHTMLEqual(
            require_module('main'), (
                '<script type="text/javascript" src="{0}" data-main="{1}">'
                '</script>').format(
                staticfiles_storage.url('js/require.js'),
                staticfiles_storage.url('js/main.js')))

    @override_settings(
        REQUIRE_DEBUG=False,
        REQUIRE_STANDALONE_MODULES={'main': {'out': 'main-built.js'}})
    def test_standalone_require_module(self):
        self.assertHTMLEqual(
            require_module('main'),
            '<script type="text/javascript" src="{0}"></script>'.format(
                staticfiles_storage.url('js/main-built.js')))

    @override_settings(
        REQUIRE_DEBUG=True,
        REQUIRE_STANDALONE_MODULES={'skin-1': {
            'relative_baseurl': 'skin_first',
            'entry_file_name': 'common1.js',
            'devel_tag': 'separate_tag',
            'out': 'skin1-built.js',
            'build_profile': 'common1-closure.build.js'}})
    def test_standalone_debug_separate(self):
        self.assertHTMLEqual(
            require_module('skin-1'), (
                '<script type="text/javascript" src="{0}"></script>'
                '<script type="text/javascript" src="{1}"></script>').format(
                staticfiles_storage.url('js/require.js'),
                staticfiles_storage.url('js/skin_first/common1.js')))

    @override_settings(
        REQUIRE_DEBUG=False,
        REQUIRE_STANDALONE_MODULES={'skin-1': {
            'relative_baseurl': 'skin_first',
            'entry_file_name': 'common1.js',
            'devel_tag': 'separate_tag',
            'out': 'skin1-built.js',
            'build_profile': 'common1-closure.build.js'}})
    def test_standalone_nodebug_separate(self):
        self.assertHTMLEqual(
            require_module('skin-1'), (
                '<script type="text/javascript" src="{0}"></script>').format(
                staticfiles_storage.url('js/skin_first/skin1-built.js')))

    @override_settings(
        REQUIRE_DEBUG=True,
        REQUIRE_STANDALONE_MODULES={'skin-1': {
            'relative_baseurl': 'skin_first',
            'entry_file_name': 'common1.js',
            'devel_tag': 'data_attr',
            'out': 'skin1-built.js',
            'build_profile': 'common1-closure.build.js'}})
    def test_standalone_debug_data_attr(self):
        self.assertHTMLEqual(
            require_module('skin-1'), (
                '<script type="text/javascript" src="{0}" data-main="{1}">'
                '</script>').format(
                staticfiles_storage.url('js/require.js'),
                staticfiles_storage.url('js/skin_first/common1.js')))

    @override_settings(
        REQUIRE_DEBUG=True,
        REQUIRE_STANDALONE_MODULES={'skin-1': {
            'relative_baseurl': 'skin_first',
            'entry_file_name': 'common1.js',
            'out': 'skin1-built.js',
            'build_profile': 'common1-closure.build.js'}})
    def test_standalone_debug_notype(self):
        self.assertHTMLEqual(
            require_module('skin-1'), (
                '<script type="text/javascript" src="{0}" data-main="{1}">'
                '</script>').format(
                staticfiles_storage.url('js/require.js'),
                staticfiles_storage.url('js/skin_first/common1.js')))

    @override_settings(
        REQUIRE_DEBUG=True,
        REQUIRE_STANDALONE_MODULES={'skin-1': {
            'relative_baseurl': 'skin_first',
            'entry_file_name': 'common1.js',
            'devel_tag': 'wharrgarbl',
            'out': 'skin1-built.js',
            'build_profile': 'common1-closure.build.js'}})
    def test_standalone_debug_garbled_type(self):
        self.assertHTMLEqual(
            require_module('skin-1'), (
                '<script type="text/javascript" src="{0}" data-main="{1}">'
                '</script>').format(
                staticfiles_storage.url('js/require.js'),
                staticfiles_storage.url('js/skin_first/common1.js')))


class OptimizedStaticFilesStorageTestsMixin(WorkingDirMixin):

    def __init__(self, *args, **kwargs):
        super(OptimizedStaticFilesStorageTestsMixin, self).__init__(
            *args, **kwargs)
        if not self.has_environment():
            skip_message = 'No {environment} present.'.format(
                environment=self.require_environment)
            self.test_collect_static = unittest.skip(
                skip_message)(self.test_collect_static)
            self.test_collect_static_build_profile = unittest.skip(
                skip_message)(self.test_collect_static_build_profile)
            self.test_collect_static_standalone = unittest.skip(
                skip_message)(self.test_collect_static_standalone)
            self.test_collect_static_standalone_build_profile = unittest.skip(
                skip_message)(
                self.test_collect_static_standalone_build_profile)

    def has_environment(self):
        try:
            return subprocess.call(
                self.require_environment_detection_args,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
        except OSError:
            return False

    def setUp(self):
        super(OptimizedStaticFilesStorageTestsMixin, self).setUp()
        self.test_resources_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'resources', 'tests'))
        resources_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'resources'))
        os.mkdir(os.path.join(WORKING_DIR, 'js'))
        shutil.copyfile(
            os.path.join(resources_dir, 'require.js'),
            os.path.join(WORKING_DIR, 'js', 'require.js'),
        )
        shutil.copyfile(
            os.path.join(self.test_resources_dir, 'main.js'),
            os.path.join(WORKING_DIR, 'js', 'main.js'),
        )
        shutil.copyfile(
            os.path.join(self.test_resources_dir, 'util.js'),
            os.path.join(WORKING_DIR, 'js', 'util.js'),
        )

    def _prepare_standalone_modules(self):
        shutil.copytree
        shutil.copytree(
            os.path.join(self.test_resources_dir, 'skin_first'),
            os.path.join(WORKING_DIR, 'js', 'skin_first'))
        shutil.copytree(
            os.path.join(self.test_resources_dir, 'skin_second'),
            os.path.join(WORKING_DIR, 'js', 'skin_second'))

    @override_settings(
        REQUIRE_STANDALONE_MODULES={}, REQUIRE_BUILD_PROFILE=None)
    def test_collect_static(self):
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command('collectstatic', interactive=False, verbosity=0)

    @override_settings(
        REQUIRE_STANDALONE_MODULES={}, REQUIRE_BUILD_PROFILE='app.build.js')
    def test_collect_static_build_profile(self):
        shutil.copyfile(
            os.path.join(self.test_resources_dir, self.test_build_profile),
            os.path.join(WORKING_DIR, 'js', 'app.build.js'),
        )
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command('collectstatic', interactive=False, verbosity=0)

    @override_settings(
        REQUIRE_BUILD_PROFILE=None,
        REQUIRE_STANDALONE_MODULES={'main': {'out': 'main-built.js'}})
    def test_collect_static_standalone(self):
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command('collectstatic', interactive=False, verbosity=0)
            self.assertTrue(
                os.path.exists(staticfiles_storage.path('js/main-built.js')))

    @override_settings(
        REQUIRE_BUILD_PROFILE=None,
        REQUIRE_STANDALONE_MODULES={
            'main': {
                'out': 'main-built.js', 'build_profile': 'main.build.js'}})
    def test_collect_static_standalone_build_profile(self):
        shutil.copyfile(
            os.path.join(
                self.test_resources_dir, self.test_standalone_build_profile),
            os.path.join(WORKING_DIR, 'js', 'main.build.js'),
        )
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command('collectstatic', interactive=False, verbosity=0)
            self.assertTrue(
                os.path.exists(staticfiles_storage.path('js/main-built.js')))

    def test_collect_static_relative_entry_points(self):
        """Test if relative entry points get compiled right."""
        self._prepare_standalone_modules()
        with self.settings(
                REQUIRE_ENVIRONMENT=self.require_environment,
                REQUIRE_STANDALONE_MODULES=self.relative_entry_point_cfg,
                REQUIRE_BUILD_PROFILE=False):
            call_command('collectstatic', interactive=False, verbosity=0)
            self.assertTrue(os.path.exists(
                staticfiles_storage.path('js/skin_first/main1-built.js')))
            self.assertTrue(os.path.exists(
                staticfiles_storage.path('js/skin_second/main2-built.js')))

    @override_settings(
        REQUIRE_BUILD_PROFILE=None,
        REQUIRE_STANDALONE_MODULES={
            'main': {
                'out': 'main-built.js', 'build_profile': 'main.build.js'}})
    def test_extra_post_process(self):
        def post_process(self, paths, *args, **kwargs):
            return ((x, x, True) for x in paths.keys())
        import django
        django.contrib.staticfiles.storage.StaticFilesStorage.post_process = \
            post_process

        shutil.copyfile(
            os.path.join(
                self.test_resources_dir, self.test_standalone_build_profile),
            os.path.join(WORKING_DIR, 'js', 'main.build.js'),
        )
        # OptimizedStaticFilesStorage.post_process = post_process
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command('collectstatic', interactive=False, verbosity=0)
            self.assertTrue(
                os.path.exists(staticfiles_storage.path('js/main-built.js')))
        del(django.contrib.staticfiles.storage.StaticFilesStorage.post_process)

    @override_settings(
        REQUIRE_BUILD_PROFILE=None,
        REQUIRE_STANDALONE_MODULES={
            'main': {
                'out': 'main-built.js', 'build_profile': 'main.build.js'}},
        REQUIRE_EXCLUDE=('js/util.js',))
    def test_collect_static_standalone_build_profile_with_excluded_file(self):
        shutil.copyfile(
            os.path.join(
                self.test_resources_dir, self.test_standalone_build_profile),
            os.path.join(WORKING_DIR, 'js', 'main.build.js'),
        )
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command('collectstatic', interactive=False, verbosity=0)
            self.assertTrue(
                os.path.exists(staticfiles_storage.path('js/main-built.js')))
            self.assertFalse(
                os.path.exists(staticfiles_storage.path('js/util.js')))

    @override_settings(
        REQUIRE_BUILD_PROFILE=False,
        REQUIRE_STANDALONE_MODULES={
            'main': {
                'out': 'main-built.js', 'build_profile': 'main.build.js'}})
    def test_collect_static_no_build_profile(self):
        """
        Test if an original file ends up in the collected dir
        unmodified.
        """
        shutil.copyfile(
            os.path.join(
                self.test_resources_dir, self.test_standalone_build_profile),
            os.path.join(WORKING_DIR, 'js', 'main.build.js'),
        )
        contents = '\n'.join((
            'function test(){',
            ' // dont uglify this',
            '}'))
        with open(os.path.join(WORKING_DIR, 'dontcompress.js'), 'w') as f:
            f.write(contents)
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command('collectstatic', interactive=False, verbosity=0)
            self.assertTrue(
                os.path.exists(staticfiles_storage.path('js/main-built.js')))

            with open(staticfiles_storage.path('dontcompress.js')) as f:
                self.assertEqual(f.read(), contents)


@override_settings(
    STATICFILES_FINDERS=(
        'django.contrib.staticfiles.finders.FileSystemFinder',),
    STATICFILES_DIRS=(WORKING_DIR,), STATIC_ROOT=OUTPUT_DIR,
    STATICFILES_STORAGE='require.storage.OptimizedStaticFilesStorage',
    REQUIRE_JS='require.js', REQUIRE_BASE_URL='js')
class OptimizedStaticFilesStorageNodeTest(
        OptimizedStaticFilesStorageTestsMixin, TestCase):

    relative_entry_point_cfg = {
        'skin-1': {
            'relative_baseurl': 'skin_first',
            'entry_file_name': 'common1.js',
            'out': 'main1-built.js',
            'build_profile': 'common1.build.js',
        },
        'skin-2': {
            'relative_baseurl': 'skin_second',
            'entry_file_name': 'common2.js',
            'out': 'main2-built.js',
            'build_profile': 'common2.build.js',
        }
    }

    require_environment_detection_args = ('node', '-v')

    require_environment = 'node'

    test_build_profile = 'app.build.js'

    test_standalone_build_profile = 'module.build.js'


@override_settings(
    STATICFILES_FINDERS=(
        'django.contrib.staticfiles.finders.FileSystemFinder',),
    STATICFILES_DIRS=(WORKING_DIR,), STATIC_ROOT=OUTPUT_DIR,
    STATICFILES_STORAGE='require.storage.OptimizedStaticFilesStorage',
    REQUIRE_JS='require.js', REQUIRE_BASE_URL='js')
class OptimizedStaticFilesStorageRhinoTest(
        OptimizedStaticFilesStorageTestsMixin, TestCase):

    relative_entry_point_cfg = {
        'skin-1': {
            'relative_baseurl': 'skin_first',
            'entry_file_name': 'common1.js',
            'devel_tag': 'separate_tag',
            'out': 'main1-built.js',
            'build_profile': 'common1-closure.build.js',
        },
        'skin-2': {
            'relative_baseurl': 'skin_second',
            'entry_file_name': 'common2.js',
            'devel_tag': 'data_attr',
            'out': 'main2-built.js',
            'build_profile': 'common2-closure.build.js',
        }
    }

    require_environment_detection_args = ('java', '-version')

    require_environment = 'rhino'

    test_build_profile = 'app.build.closure.js'

    test_standalone_build_profile = 'module.build.closure.js'


class EmptyEnvironment(AutoEnvironment):

    """Empty environment class to test AutoEnvironment."""
    environments = []


class EmptyEnvironmentTest(TestCase):

    """Tests for AutoEnvironment where environment itself is empty."""

    def setUp(self):
        self.empty_environment = EmptyEnvironment([])

    def test_empty_environment_variable(self):
        """
        Test if the environment variable can raise an
        EnvironmentError().
        """
        with self.assertRaisesMessage(
                EnvironmentError, 'no environments detected:'):
            self.empty_environment.environment

    def test_empty_environment_args(self):
        """
        Test if the args function raises an error with our empty class.
        """
        with self.assertRaisesMessage(
                EnvironmentError, 'no environments detected:'):
            self.empty_environment.args()


class AutoEnvironmentTest(TestCase):

    """Tests for AutoEnvironment."""

    def setUp(self):
        self.auto_environment = AutoEnvironment([])

    def test_parent_environment_args_raises_notimplemented(self):
        """
        Test if the root Environment class' args() function raises
        a NotImplementedError.
        """
        with self.assertRaises(NotImplementedError):
            super(AutoEnvironment, self.auto_environment).args()

    def test_serves_an_environment(self):
        """
        Test if the enviroment cached property serves us an environment.
        """
        environment = self.auto_environment.environment
        self.assertIsInstance(environment, Environment)


class TemporaryCompileEnvironmentTest(TestCase):

    """
    Tests for TemporaryCompileEnvironment.
    """

    def setUp(self):
        self.patch_loadenv = mock.patch('require.storage.load_environment')
        self.mock_loadenv = self.patch_loadenv.start()
        self.patch_subprocesscall = mock.patch(
            'require.storage.subprocess.call')
        self.mock_subprocesscall = self.patch_subprocesscall.start()

        self.mock_loadenv.return_value.return_value.args.return_value = ['1']

    def tearDown(self):
        self.patch_loadenv.stop()
        self.patch_subprocesscall.stop()

    def test_set_default_loglevel(self):
        """
        Test if run_optimizer sets a default loglevel AND raises an
        OptimizationError.
        """
        environment = TemporaryCompileEnvironment(verbosity=0)
        with self.assertRaisesMessage(
                OptimizationError, 'Error while running r.js optimizer.'):
            environment.run_optimizer()
        self.assertTrue(self.mock_loadenv.called)
        self.assertEqual(
            self.mock_loadenv.return_value.call_args, mock.call(environment))
        self.assertEqual(
            self.mock_loadenv.return_value.return_value.args.call_count, 1)
        self.assertEqual(
            self.mock_loadenv.return_value.return_value.args.return_value[0],
            '1')
        self.assertRegexpMatches(
            self.mock_loadenv.return_value.return_value.args.return_value[1],
            r'.*require/resources/r.js$')
        self.assertEqual(
            self.mock_loadenv.return_value.return_value.args.return_value[2:4],
            ['-o', 'logLevel=4'])
        self.mock_subprocesscall.assert_called_once_with(
            self.mock_loadenv.return_value.return_value.args.return_value)


class OptimizedFilesMixinTest(TestCase):

    """Test for OptimizedFilesMixinTest."""

    def setUp(self):
        self.optimized_mixin = OptimizedFilesMixin()

    def test_post_process_raises_stopiteration(self):
        """
        On dry_run=True, post_process() should return an empty iterator.
        """
        return_iterator = self.optimized_mixin.post_process(
            'foo', dry_run=True)
        count = 0
        for count, item in enumerate(return_iterator):
            pass
        self.assertEqual(count, 0)

    @override_settings(
        REQUIRE_STANDALONE_MODULES={'a': {}}, REQUIRE_BASE_URL='js',
        REQUIRE_BUILD_PROFILE=None)
    def test_iterator_raises_improperlyconfigured(self):
        paths = {
            'js/file1': (mock.Mock(), 'js/file1'),
            'js/file2': (mock.Mock(), 'js/file2'),
        }
        paths['js/file1'][0].open.return_value.read.return_value = \
            b'file1_content'
        paths['js/file2'][0].open.return_value.read.return_value = \
            b'file2_content'
        return_iterator = self.optimized_mixin.post_process(paths)
        with self.assertRaisesMessage(
                ImproperlyConfigured,
                'No \'out\' option specified for module \'a\' in '
                'REQUIRE_STANDALONE_MODULES setting'):
            count, item = enumerate(return_iterator)
        paths['js/file1'][0].open.assert_called_with('js/file1', 'rb')
        paths['js/file2'][0].open.assert_called_with('js/file2', 'rb')
