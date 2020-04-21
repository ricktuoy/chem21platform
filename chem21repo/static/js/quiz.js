// Place third party dependencies in the lib folder
//
// Configure loading modules from the lib directory,
// except 'app' ones, 
requirejs.config({
    "urlArgs": "bust=005"
});
// Load the main app module to start the app
requirejs(["quiz/main"]);