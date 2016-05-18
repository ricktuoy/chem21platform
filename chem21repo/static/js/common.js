// Place third party dependencies in the lib folder
//
// Configure loading modules from the lib directory,
// except 'app' ones, 
requirejs.config({
    "baseUrl": "/static/js/lib",
    "urlArgs": "bust=008",
    "shim": {
        'jquery.colorbox': ['jquery'],
        'jquery.throttle-debounce': ['jquery'],
        "jquery.mobile.config": ["jquery"],
        'jquery.mobile': ['jquery','jquery.mobile.config']
    }
});
// Load the main app module to start the app
requirejs(["../common/main"]);