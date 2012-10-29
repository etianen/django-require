from django.conf import settings


REQUIRE_BUILD_PROFILE = getattr(settings, "REQUIRE_BUILD_PROFILE", "js/app.build.js")