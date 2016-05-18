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
        'jquery.mobile': ['jquery']
    }
});
// Load the main app module to start the app
requirejs(["../common/main"]);