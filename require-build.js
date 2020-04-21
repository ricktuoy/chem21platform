({
    
    /*
     * List the modules that will be optimized. All their immediate and deep
     * dependencies will be included in the module's file when the build is
     * done. A minimum module entry is {name: "module_name"}.
     */
        baseUrl: "js",
        appDir: "collected-static/src",
        dir: "collected-static/deploy",
        modules: [{name: 'file_listing'},
                  {name: 'front_admin'},
                  {name: 'quiz'}, 
                  {name: 'guide'},
                  {name: 'glossary'},
                  {name: 'list_fix'},
                  {name: 'common'},
                  {name: 'common2'},
                  {name: 'flow_chart'},
                  {name: 'mol_menu'},
                  {name: 'mol_menu_admin'},
                  {name: 'select_bibliotag'},
                  {name: 'select_figuretag'},
                  {name: 'select_linktag'},
                  {name: 'admin_fileupload'},
                  {name: 'google_picker'},
                  {name: 'selector_widget_mixin'},
                  {name: 'page_menu'},
                  {name: 'nav_reorder'}],
    /*
     * Allow CSS optimizations. Allowed values:
     * - "standard": @import inlining, comment removal and line returns.
     * Removing line returns may have problems in IE, depending on the type
     * of CSS.
     * - "standard.keepLines": Like "standard" but keeps line returns.
     * - "none": Skip CSS optimizations.
     * - "standard.keepComments": Keeps the file comments, but removes line returns.
     * - "standard.keepComments.keepLines": Keeps the file comments and line returns.
     */
    optimizeCss: "none",
    /*
     * How to optimize all the JS files in the build output directory.
     * Right now only the following values are supported:
     * - "uglify": Uses UglifyJS to minify the code.
     * - "uglify2": Uses UglifyJS2.
     * - "closure": Uses Google's Closure Compiler in simple optimization
     * mode to minify the code. Only available if REQUIRE_ENVIRONMENT is "rhino" (the default).
     * - "none": No minification will be done.
     */
    optimize: "none",
    /*
     * By default, comments that have a license in them are preserved in the
     * output. However, for a larger built files there could be a lot of
     * comment files that may be better served by having a smaller comment
     * at the top of the file that points to the list of all the licenses.
     * This option will turn off the auto-preservation, but you will need
     * work out how best to surface the license information.
     */
    preserveLicenseComments: true,
    /*
     * The default behaviour is to optimize the build layers (the "modules"
     * section of the config) and any other JS file in the directory. However, if
     * the non-build layer JS files will not be loaded after a build, you can
     * skip the optimization of those files, to speed up builds. Set this value
     * to true if you want to skip optimizing those other non-build layer JS
     * files.
     */
    skipDirOptimize: true,
    paths: {
        "jquery": "lib/jquery",
        "jquery.colorbox": "lib/jquery.colorbox",
        "jquery.mjs.nestedSortable": "lib/jquery.mjs.nestedSortable",
        "jquery-ui": "lib/jquery-ui",
        "jquery.cookie": "lib/jquery.cookie",
        "jquery.ui-contextmenu": "lib/jquery.ui-contextmenu",
        "jquery.fileupload": "lib/jquery.fileupload",
        "jquery.mobile": "lib/jquery.mobile/jquery.mobile-1.4.5",
        "jquery.mobile.config": "lib/jquery.mobile/jquery.mobile.config",
        "jquery.throttle-debounce": "lib/jquery.throttle-debounce",
        "popcorn": "lib/popcorn",
        "quiz": "quiz",
        "guide": "guide/main",
        "file_listing": "file_listing",
        "list_fix": "list-fix",
        "mol_menu": "mol-menu",
        "mol_menu_admin": "mol-menu-admin",
        "flow_chart": "flow-chart",
        "common": "common",
        "common2": "common2",
        "glossary": "glossary/main",
        "front_admin": "front-admin",
        "select_bibliotag": "../tiny_mce/plugins/bibliotag/js/select_bibliotag",
        "select_figuretag": "../tiny_mce/plugins/figuretag/js/select_figuretag",
        "select_linktag": "../tiny_mce/plugins/linktag/js/select_linktag",
        "google_picker": "google-picker/main",
        "uri_js": "lib/uri.js/src",
        "jsCurry": "lib/jscurry-0.4.1",
        "jquery.math": "lib/jqmath-0.4.4" ,
        "admin_fileupload": "admin-fileupload",
        "nav_reorder": "nav-reorder",
        "pdf_gen": "pdf-gen",
        "selector_widget_mixin": "selector-widget-mixin/main",
        "page_menu": "page-menu"
    },
    shim: {
        "jquery.math": ['jquery','jsCurry']
    }
})
