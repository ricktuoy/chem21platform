// Place third party dependencies in the lib folder
//
// Configure loading modules from the lib directory,
// except 'app' ones, 
requirejs.config({
    "urlArgs": "bust=017",
    "shim": {
        'jquery.colorbox': ['jquery'],
        'jquery.throttle-debounce': ['jquery'],
        "jquery.mobile.config": ["jquery"],
        'jquery.mobile': ['jquery','jquery.mobile.config'],
        "uri_js/jquery.URI": ['jquery', 'URI'],
        "popcorn": {'exports': 'Popcorn'}
    }
});
// Load the main app module to start the app
requirejs(["common/main"]);