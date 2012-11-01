/**
 * Build profile for a standalone django-require module, packaged with almond.js.
 * 
 * This supports all the normal configuration available to a r.js build profile. The only gotchas are:
 *
 *   - 'baseUrl' will be overidden by django-require during the build process.
 *   - 'name' will be overidden by django-require during the build process.
 *   - 'include' will be overidden by django-require during the build process.
 *   - 'out' will be overidden by django-require during the build process. 
 */
({
    optimize: "closure",
    wrap: true
})