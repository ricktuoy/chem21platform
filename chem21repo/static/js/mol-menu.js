// Place third party dependencies in the lib folder
//
// Configure loading modules from the lib directory,
// except 'app' ones, 
requirejs.config({
    "urlArgs": "bust=003",
    "shim": {
        'jquery.colorbox': ['jquery']
    }
});
// Load the main app module to start the app
requirejs(["mol-menu/main"]);