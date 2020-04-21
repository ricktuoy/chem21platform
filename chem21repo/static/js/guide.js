// Place third party dependencies in the lib folder
//
// Configure loading modules from the lib directory,
// except 'app' ones, 
requirejs.config({
    "urlArgs": "bust=009"
});
// Load the main app module to start the app
requirejs(["guide/main"]);