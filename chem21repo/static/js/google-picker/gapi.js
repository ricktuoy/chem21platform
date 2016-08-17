define(['settings'], function(config) {  
  function ApiManager() {
    this.loadGapi();
  }

  ApiManager.prototype.init = function() {
  	  var self = this;

	  gapi.client.load('tasks', 'v1', function() { /* Loaded */ });

	  function handleClientLoad() {
	    gapi.client.setApiKey(config.apiKey);
	    window.setTimeout(checkAuth, 100);
	  }

	  function checkAuth() {
	    gapi.auth.authorize({ client_id: config.clientId, scope: config.scopes, immediate: true }, handleAuthResult);
	  }

	  function handleAuthResult(authResult) {
	  	var oauthToken = False;
	  	if (authResult && !authResult.error) {      
        	oauthToken = authResult.access_token;
        	createPicker();
      	}
      	if (oauthToken) {
	        var view = new google.picker.View(google.picker.ViewId.DOCS);
	        view.setMimeTypes("application/vnd.google-apps.document");
	        var picker = new google.picker.PickerBuilder()
	            .enableFeature(google.picker.Feature.NAV_HIDDEN)
	            .setAppId(settings.appId)
	            .setOAuthToken(oauthToken)
	            .addView(view)
	            .addView(new google.picker.DocsUploadView())
	            .setDeveloperKey(settings.developerKey)
	            .setCallback(pickerCallback)
	            .build();
	         $gpicker.data("picker", picker);
	         $gpicker.removeClass("disabled");
      	}
	  }

	  handleClientLoad();
  };

  ApiManager.prototype.loadGapi = function() {
  	var self = this;

	  // Don't load gapi if it's already present
	  if (typeof gapi !== 'undefined') {
	    return this.init();
	  }

	  require(['https://apis.google.com/js/client.js?onload=define'], function() {
	    // Poll until gapi is ready
	    function checkGAPI() {
	      if (gapi && gapi.client) {
	        self.init();
	      } else {
	        setTimeout(checkGAPI, 100);
	      }
	    }

	    checkGAPI();
	  });
  };

  return ApiManager;
});