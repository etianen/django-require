import tempfile, shutil, os.path, subprocess, unittest

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.management import call_command
from django.test import TestCase

from require.conf import settings as require_settings
from require.storage import OptimizedStaticFilesStorage
from require.templatetags.require import require_module


class TestableFileSystemFinder(FileSystemFinder):
    
    """
    This finder re-inits at the start of each method, allowing the STATICFILES_DIRS
    settings to be overridden at runtime.
    """
    
    def find(self, *args, **kwargs):
        self.__init__()
        return super(TestableFileSystemFinder, self).find(*args, **kwargs)

    def find_location(self, *args, **kwargs):
        self.__init__()
        return super(TestableFileSystemFinder, self).find_location(*args, **kwargs)

    def list(self, *args, **kwargs):
        self.__init__()
        return super(TestableFileSystemFinder, self).list(*args, **kwargs)


class TestableOptimizedStaticFilesStorage(OptimizedStaticFilesStorage):
    
    """
    The location property for this storage is dynamically looked up from
    the django settings object, allowing it to be overridden at runtime.
    """
    
    @property
    def location(self):
        return settings.STATIC_ROOT
    
    @location.setter
    def location(self, value):
        pass


class WorkingDirMixin(object):

    def __init__(self, *args, **kwargs):
        super(WorkingDirMixin, self).__init__(*args, **kwargs)
        self._working_dirs = []

    def _make_working_dir(self):
        working_dir = tempfile.mkdtemp()
        self._working_dirs.append(working_dir)
        return working_dir

    def setUp(self):
        self.working_dir = self._make_working_dir()

    def tearDown(self):
        for working_dir in self._working_dirs:
            shutil.rmtree(working_dir, ignore_errors=True)
        self._working_dirs = []


class RequireInitTest(WorkingDirMixin, TestCase):

    def testCopyRequire(self):
        with self.settings(STATICFILES_DIRS=(self.working_dir,), REQUIRE_JS="require.js"):
            call_command("require_init", verbosity=0)
            self.assertTrue(os.path.exists(os.path.join(self.working_dir, require_settings.REQUIRE_BASE_URL, "require.js")))

    def testCopyRequireRelative(self):
        with self.settings(STATICFILES_DIRS=(self.working_dir,), REQUIRE_JS="../require.js"):
            call_command("require_init", verbosity=0)
            self.assertTrue(os.path.exists(os.path.abspath(os.path.join(self.working_dir, require_settings.REQUIRE_BASE_URL, "..", "require.js"))))

    def testCopyBuildProfile(self):
        build_profile = "app.build.js"
        with self.settings(STATICFILES_DIRS=(self.working_dir,), REQUIRE_BUILD_PROFILE=build_profile):
            call_command("require_init", verbosity=0)
            self.assertTrue(os.path.exists(os.path.join(self.working_dir, require_settings.REQUIRE_BASE_URL, build_profile)))

    def testCopyStandaloneProfile(self):
        standalone_profile = "module.build.js"
        with self.settings(STATICFILES_DIRS=(self.working_dir,), REQUIRE_STANDALONE_MODULES={"main": {"build_profile": standalone_profile}}):
            call_command("require_init", verbosity=0)
            self.assertTrue(os.path.exists(os.path.join(self.working_dir, require_settings.REQUIRE_BASE_URL, standalone_profile)))

    def testCopyRequireCustomDir(self):
        with self.settings(REQUIRE_JS="require.js"):
            call_command("require_init", dir=self.working_dir, verbosity=0)
            self.assertTrue(os.path.exists(os.path.join(self.working_dir, require_settings.REQUIRE_BASE_URL, "require.js")))


class RequireModuleTest(TestCase):

    def testRequireModule(self):
        with self.settings(REQUIRE_JS="require.js", REQUIRE_BASE_URL="js", REQUIRE_STANDALONE_MODULES={}):
            self.assertHTMLEqual(require_module("main"), """<script src="{0}" data-main="{1}"></script>""".format(
                staticfiles_storage.url("js/require.js"),
                staticfiles_storage.url("js/main.js"),
            ))

    def testStandaloneRequireModule(self):
        with self.settings(REQUIRE_JS="require.js", REQUIRE_BASE_URL="js", REQUIRE_DEBUG=False, REQUIRE_STANDALONE_MODULES={"main": {"out": "main-built.js"}}):
            self.assertHTMLEqual(require_module("main"), """<script src="{0}"></script>""".format(
                staticfiles_storage.url("js/main-built.js"),
            ))


class OptimizedStaticFilesStorageTestsMixin(WorkingDirMixin):

    def __init__(self, *args, **kwargs):
        super(OptimizedStaticFilesStorageTestsMixin, self).__init__(*args, **kwargs)
        if not self.has_environment():
            skip_message = "No {environment} present.".format(environment=self.require_environment)
            self.testCollectStatic = unittest.skip(skip_message)(self.testCollectStatic)
            self.testCollectStaticBuildProfile = unittest.skip(skip_message)(self.testCollectStaticBuildProfile)
            self.testCollectStaticStandalone = unittest.skip(skip_message)(self.testCollectStaticStandalone)
            self.testCollectStaticStandaloneBuildProfile = unittest.skip(skip_message)(self.testCollectStaticStandaloneBuildProfile)

    def has_environment(self):
        try:
            return subprocess.call(self.require_environment_detection_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
        except OSError:
            return False

    def setUp(self):
        super(OptimizedStaticFilesStorageTestsMixin, self).setUp()
        self.output_dir = self._make_working_dir()
        self.test_resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources", "tests"))
        resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources"))
        os.mkdir(os.path.join(self.working_dir, "js"))
        shutil.copyfile(
            os.path.join(resources_dir, "require.js"),
            os.path.join(self.working_dir, "js", "require.js"),
        )
        shutil.copyfile(
            os.path.join(self.test_resources_dir, "main.js"),
            os.path.join(self.working_dir, "js", "main.js"),
        )
        shutil.copyfile(
            os.path.join(self.test_resources_dir, "util.js"),
            os.path.join(self.working_dir, "js", "util.js"),
        )

    def testCollectStatic(self):
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment, STATICFILES_FINDERS=("require.tests.TestableFileSystemFinder",), STATICFILES_DIRS=(self.working_dir,), STATIC_ROOT=self.output_dir, STATICFILES_STORAGE="require.tests.TestableOptimizedStaticFilesStorage", REQUIRE_JS="require.js", REQUIRE_BASE_URL="js", REQUIRE_STANDALONE_MODULES={}, REQUIRE_BUILD_PROFILE=None):
            call_command("collectstatic", interactive=False, verbosity=0)

    def testCollectStaticBuildProfile(self):
        shutil.copyfile(
            os.path.join(self.test_resources_dir, self.test_build_profile),
            os.path.join(self.working_dir, "js", "app.build.js"),
        )
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment, STATICFILES_FINDERS=("require.tests.TestableFileSystemFinder",), STATICFILES_DIRS=(self.working_dir,), STATIC_ROOT=self.output_dir, STATICFILES_STORAGE="require.tests.TestableOptimizedStaticFilesStorage", REQUIRE_JS="require.js", REQUIRE_BASE_URL="js", REQUIRE_STANDALONE_MODULES={}, REQUIRE_BUILD_PROFILE="app.build.js"):
            call_command("collectstatic", interactive=False, verbosity=0)

    def testCollectStaticStandalone(self):
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment, STATICFILES_FINDERS=("require.tests.TestableFileSystemFinder",), STATICFILES_DIRS=(self.working_dir,), STATIC_ROOT=self.output_dir, STATICFILES_STORAGE="require.tests.TestableOptimizedStaticFilesStorage", REQUIRE_JS="require.js", REQUIRE_BUILD_PROFILE=None, REQUIRE_BASE_URL="js", REQUIRE_STANDALONE_MODULES={"main": {"out": "main-built.js"}}):
            call_command("collectstatic", interactive=False, verbosity=0)
            self.assertTrue(os.path.exists(os.path.join(self.output_dir, "js", "main-built.js")))

    def testCollectStaticStandaloneBuildProfile(self):
        shutil.copyfile(
            os.path.join(self.test_resources_dir, self.test_standalone_build_profile),
            os.path.join(self.working_dir, "js", "main.build.js"),
        )
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment, STATICFILES_FINDERS=("require.tests.TestableFileSystemFinder",), STATICFILES_DIRS=(self.working_dir,), STATIC_ROOT=self.output_dir, STATICFILES_STORAGE="require.tests.TestableOptimizedStaticFilesStorage", REQUIRE_JS="require.js", REQUIRE_BUILD_PROFILE=None, REQUIRE_BASE_URL="js", REQUIRE_STANDALONE_MODULES={"main": {"out": "main-built.js", "build_profile": "main.build.js"}}):
            call_command("collectstatic", interactive=False, verbosity=0)
            self.assertTrue(os.path.exists(os.path.join(self.output_dir, "js", "main-built.js")))


class OptimizedStaticFilesStorageNodeTest(OptimizedStaticFilesStorageTestsMixin, TestCase):

    require_environment_detection_args = ("node", "-v")

    require_environment = "node"

    test_build_profile = "app.build.js"

    test_standalone_build_profile = "module.build.js"


class OptimizedStaticFilesStorageRhinoTest(OptimizedStaticFilesStorageTestsMixin, TestCase):

    require_environment_detection_args = ("java", "-version")

    require_environment = "rhino"

    test_build_profile = "app.build.closure.js"

    test_standalone_build_profile = "module.build.closure.js"
