/**
 * Build profile for django-require.
 * 
 * This supports all the normal configuration available to a r.js build profile. The only gotchas are:
 * 
 *   - The output 'dir' will be overidden by django-require during build. Just leave this setting out. 
 */
({
    appDir: "../",
    baseUrl: "js",
    optimize: "closure",
    optimizeCss: "standard",
    modules: []
})