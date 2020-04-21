// Place third party dependencies in the lib folder
//
// Configure loading modules from the lib directory,
// except 'app' ones, 
requirejs.config({
    "urlArgs": "bust=005",
});
// Load the main app module to start the app
require(["./front-admin/main"],
	function(App) {
		require(['https://apis.google.com/js/client.js?onload=define'], App.Picker.load);
	}
);