// Place third party dependencies in the lib folder
//
// Configure loading modules from the lib directory,
// except 'app' ones, 
requirejs.config({
    "baseUrl": "/static/js/lib",
    "urlArgs": "bust=001"
});
// Load the main app module to start the app
requirejs(["../selector-widget-mixin/main"]);