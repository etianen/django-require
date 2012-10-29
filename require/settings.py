from django.conf import settings


REQUIRE_BASE_URL = getattr(settings, "REQUIRE_BASE_URL", "js")

REQUIRE_BUILD_PROFILE = getattr(settings, "REQUIRE_BUILD_PROFILE", "app.build.js")

REQUIRE_APP_VERSION = getattr(settings, "REQUIRE_APP_VERSION", None)

REQUIRE_DEBUG = getattr(settings, "REQUIRE_DEBUG", settings.DEBUG)