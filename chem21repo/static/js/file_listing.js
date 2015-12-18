// Place third party dependencies in the lib folder
//
// Configure loading modules from the lib directory,
// except 'app' ones, 
requirejs.config({
    "baseUrl": "/static/js/lib",
    "shim": {
        'jquery.colorbox': ['jquery'],
    }
});
// Load the main app module to start the app
requirejs(["file_listing/main"]);