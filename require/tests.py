from __future__ import unicode_literals

import tempfile, shutil, os.path, subprocess, unittest

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from django.template import Context, Template

from require.conf import settings as require_settings

WORKING_DIR = tempfile.mkdtemp()
OUTPUT_DIR = tempfile.mkdtemp()


class WorkingDirMixin(object):

    def tearDown(self):
        for working_dir in (WORKING_DIR, OUTPUT_DIR):
            for name in os.listdir(working_dir):
                path = os.path.join(working_dir, name)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            assert len(os.listdir(working_dir)) == 0


class RequireInitTest(WorkingDirMixin, TestCase):

    @override_settings(STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_JS="require.js")
    def testCopyRequire(self):
        call_command("require_init", verbosity=0)
        self.assertTrue(os.path.exists(os.path.join(WORKING_DIR, require_settings.REQUIRE_BASE_URL, "require.js")))

    @override_settings(STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_JS="../require.js")
    def testCopyRequireRelative(self):
        call_command("require_init", verbosity=0)
        self.assertTrue(os.path.exists(os.path.abspath(os.path.join(WORKING_DIR, require_settings.REQUIRE_BASE_URL, "..", "require.js"))))

    @override_settings(STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_BUILD_PROFILE="app.build.js")
    def testCopyBuildProfile(self):
        call_command("require_init", verbosity=0)
        self.assertTrue(os.path.exists(os.path.join(WORKING_DIR, require_settings.REQUIRE_BASE_URL, "app.build.js")))

    @override_settings(STATICFILES_DIRS=(WORKING_DIR,), REQUIRE_STANDALONE_MODULES={"main": {"build_profile": "module.build.js"}})
    def testCopyStandaloneProfile(self):
        call_command("require_init", verbosity=0)
        self.assertTrue(os.path.exists(os.path.join(WORKING_DIR, require_settings.REQUIRE_BASE_URL, "module.build.js")))

    @override_settings(REQUIRE_JS="require.js")
    def testCopyRequireCustomDir(self):
        call_command("require_init", dir=WORKING_DIR, verbosity=0)
        self.assertTrue(os.path.exists(os.path.join(WORKING_DIR, require_settings.REQUIRE_BASE_URL, "require.js")))


@override_settings(REQUIRE_JS="require.js", REQUIRE_BASE_URL="js")
class RequireModuleTest(TestCase):

    def renderTemplate(self):
        return Template("{% load require %}{% require_module 'main' %}").render(Context({}))

    @override_settings(REQUIRE_STANDALONE_MODULES={})
    def testRequireModule(self):
        self.assertHTMLEqual(self.renderTemplate(), """<script src="{0}" data-main="{1}"></script>""".format(
            staticfiles_storage.url("js/require.js"),
            staticfiles_storage.url("js/main.js"),
        ))

    @override_settings(REQUIRE_DEBUG=False, REQUIRE_STANDALONE_MODULES={"main": {"out": "main-built.js"}})
    def testStandaloneRequireModule(self):
        self.assertHTMLEqual(self.renderTemplate(), """<script src="{0}"></script>""".format(
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
        self.test_resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources", "tests"))
        resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources"))
        os.mkdir(os.path.join(WORKING_DIR, "js"))
        shutil.copyfile(
            os.path.join(resources_dir, "require.js"),
            os.path.join(WORKING_DIR, "js", "require.js"),
        )
        shutil.copyfile(
            os.path.join(self.test_resources_dir, "main.js"),
            os.path.join(WORKING_DIR, "js", "main.js"),
        )
        shutil.copyfile(
            os.path.join(self.test_resources_dir, "util.js"),
            os.path.join(WORKING_DIR, "js", "util.js"),
        )

    @override_settings(REQUIRE_STANDALONE_MODULES={}, REQUIRE_BUILD_PROFILE=None)
    def testCollectStatic(self):
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command("collectstatic", interactive=False, verbosity=0)

    @override_settings(REQUIRE_STANDALONE_MODULES={}, REQUIRE_BUILD_PROFILE="app.build.js")
    def testCollectStaticBuildProfile(self):
        shutil.copyfile(
            os.path.join(self.test_resources_dir, self.test_build_profile),
            os.path.join(WORKING_DIR, "js", "app.build.js"),
        )
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command("collectstatic", interactive=False, verbosity=0)

    @override_settings(REQUIRE_BUILD_PROFILE=None, REQUIRE_STANDALONE_MODULES={"main": {"out": "main-built.js"}})
    def testCollectStaticStandalone(self):
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command("collectstatic", interactive=False, verbosity=0)
            self.assertTrue(os.path.exists(staticfiles_storage.path("js/main-built.js")))

    @override_settings(REQUIRE_BUILD_PROFILE=None, REQUIRE_STANDALONE_MODULES={"main": {"out": "main-built.js", "build_profile": "main.build.js"}})
    def testCollectStaticStandaloneBuildProfile(self):
        shutil.copyfile(
            os.path.join(self.test_resources_dir, self.test_standalone_build_profile),
            os.path.join(WORKING_DIR, "js", "main.build.js"),
        )
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command("collectstatic", interactive=False, verbosity=0)
            self.assertTrue(os.path.exists(staticfiles_storage.path("js/main-built.js")))

    @override_settings(REQUIRE_BUILD_PROFILE=False, REQUIRE_STANDALONE_MODULES={"main": {"out": "main-built.js", "build_profile": "main.build.js"}})
    def testCollectStaticNoBuildProfile(self):
        shutil.copyfile(
            os.path.join(self.test_resources_dir, self.test_standalone_build_profile),
            os.path.join(WORKING_DIR, "js", "main.build.js"),
        )
        contents = """
function test(){
    // dont uglify this
};
"""
        with open(os.path.join(WORKING_DIR, 'dontcompress.js'), 'w') as f:
            f.write(contents)
        with self.settings(REQUIRE_ENVIRONMENT=self.require_environment):
            call_command("collectstatic", interactive=False, verbosity=0)
            self.assertTrue(os.path.exists(staticfiles_storage.path("js/main-built.js")))

            with open(staticfiles_storage.path('dontcompress.js')) as f:
                self.assertEqual(f.read(), contents)


@override_settings(STATICFILES_FINDERS=("django.contrib.staticfiles.finders.FileSystemFinder",), STATICFILES_DIRS=(WORKING_DIR,), STATIC_ROOT=OUTPUT_DIR, STATICFILES_STORAGE="require.storage.OptimizedStaticFilesStorage", REQUIRE_JS="require.js", REQUIRE_BASE_URL="js")
class OptimizedStaticFilesStorageNodeTest(OptimizedStaticFilesStorageTestsMixin, TestCase):

    require_environment_detection_args = ("node", "-v")

    require_environment = "node"

    test_build_profile = "app.build.js"

    test_standalone_build_profile = "module.build.js"


@override_settings(STATICFILES_FINDERS=("django.contrib.staticfiles.finders.FileSystemFinder",), STATICFILES_DIRS=(WORKING_DIR,), STATIC_ROOT=OUTPUT_DIR, STATICFILES_STORAGE="require.storage.OptimizedStaticFilesStorage", REQUIRE_JS="require.js", REQUIRE_BASE_URL="js")
class OptimizedStaticFilesStorageRhinoTest(OptimizedStaticFilesStorageTestsMixin, TestCase):

    require_environment_detection_args = ("java", "-version")

    require_environment = "rhino"

    test_build_profile = "app.build.closure.js"

    test_standalone_build_profile = "module.build.closure.js"
