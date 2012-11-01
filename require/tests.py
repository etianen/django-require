import tempfile, shutil, os.path

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.test import TestCase

from require.conf import settings as require_settings
from require.templatetags.require import require_module


class RequireInitTest(TestCase):
    
    def setUp(self):
        self.working_dir = tempfile.mkdtemp()
    
    def testCopyRequire(self):
        with self.settings(STATICFILES_DIRS=(self.working_dir,), REQUIRE_JS="require.js"):
            call_command("require_init", verbosity=0)
            self.assertTrue(os.path.exists(os.path.join(self.working_dir, require_settings.REQUIRE_BASE_URL, "require.js")))
    
    def testCopyRequireRelative(self):
        with self.settings(STATICFILES_DIRS=(self.working_dir,), REQUIRE_JS="../require.js"):
            call_command("require_init", verbosity=0)
            self.assertTrue(os.path.exists(os.path.join(self.working_dir, require_settings.REQUIRE_BASE_URL, "..", "require.js")))
            
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
    
    def tearDown(self):
        shutil.rmtree(self.working_dir, ignore_errors=True)
        
        
class RequireModuleTest(TestCase):
    
    def testRequireModule(self):
        with self.settings(REQUIRE_JS="require.js", REQUIRE_BASE_URL="js", REQUIRE_STANDALONE_MODULES={}):
            self.assertHTMLEqual(require_module("main"), """<script src="{}" data-main="{}"></script>""".format(
                staticfiles_storage.url("js/require.js"),
                staticfiles_storage.url("js/main.js"),
            ))
            
    def testStandaloneRequireModule(self):
        with self.settings(REQUIRE_JS="require.js", REQUIRE_BASE_URL="js", REQUIRE_STANDALONE_MODULES={"main": {"out": "main-built.js"}}):
            self.assertHTMLEqual(require_module("main"), """<script src="{}"></script>""".format(
                staticfiles_storage.url("js/main-built.js"),
            ))