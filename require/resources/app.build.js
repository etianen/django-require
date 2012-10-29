/**
 * Build profile for django-require.
 * 
 * This supports all the normal configuration available to a r.js build profile. The only gotchas are:
 *
 *   - 'baseUrl' will be overidden by django-require during the build process.
 *   - 'appDir' will be overidden by django-require during the build process.
 *   - 'dir' will be overidden by django-require during the build process. 
 */
({
    optimize: "closure",
    optimizeCss: "standard",
    preserveLicenseComments: false,
    modules: []
})