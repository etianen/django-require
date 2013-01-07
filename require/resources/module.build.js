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
    
    /*
     * Wraps the module in an anonymous function to remove require() and define()
     * from the global namespace. Set to false if you wish to use these functions
     * outside of your standalone module.
     */ 
    wrap: true,
    
    /*
     * How to optimize all the JS files in the build output directory.
     * Right now only the following values are supported:
     * - "uglify": Uses UglifyJS to minify the code.
     * - "uglify2": Uses UglifyJS2.
     * - "closure": Uses Google's Closure Compiler in simple optimization
     * mode to minify the code. Only available if REQUIRE_ENVIRONMENT is "rhino" (the default).
     * - "none": No minification will be done.
     */
    optimize: "uglify2",
    
    /*
     * By default, comments that have a license in them are preserved in the
     * output. However, for a larger built files there could be a lot of
     * comment files that may be better served by having a smaller comment
     * at the top of the file that points to the list of all the licenses.
     * This option will turn off the auto-preservation, but you will need
     * work out how best to surface the license information.
     */
    preserveLicenseComments: true
    
})