define(["jquery","google-picker/settings"], function($,settings) {

    var pickerApiLoaded = false;
    var oauthToken;
    var $gpicker = $("#gpicker_trigger");



    function onAuthApiLoad() {
      window.gapi.auth.authorize(
          {
            'client_id': settings.clientId,
            'scope': settings.scopes,
            'immediate': false
          },
          handleAuthResult);
    }

    function onPickerApiLoad() {
      pickerApiLoaded = true;
      createPicker();
    }

    function handleAuthResult(authResult) {
      if (authResult && !authResult.error) {      
        oauthToken = authResult.access_token;
        createPicker();
      }
    }

    // Create and render a Picker object for searching images.
    function createPicker() {
      if (pickerApiLoaded && oauthToken) {
        var view = new google.picker.View(google.picker.ViewId.DOCS);
        view.setMimeTypes("application/vnd.google-apps.document");
        var picker = new google.picker.PickerBuilder()
            .enableFeature(google.picker.Feature.NAV_HIDDEN)
            .setAppId(settings.appId)
            .setOAuthToken(oauthToken)
            .addView(view)
            .addView(new google.picker.DocsUploadView())
            .setDeveloperKey(settings.apiKey)
            .setCallback(pickerCallback)
            .build();
         $gpicker.data("picker", picker);
         $gpicker.removeClass("disabled");
      }
    }
    
    $gpicker.on("click", function(event) {
      var picker = $(this).data("picker");
      if(picker) {
        picker.setVisible(true);
      };
      event.preventDefault();
    });

    if(!$gpicker.data("picker")) {
      $gpicker.addClass("disabled");
    }


    // A simple callback implementation.
    function pickerCallback(data) {
      if (data.action == google.picker.Action.PICKED) {
        var fileId = data.docs[0].id;
        $.getJSON(settings.server_uri+"/"+fileId, function(data) {
          location.reload();
        });
      }
    }

        // Use the Google API Loader script to load the google.picker script.
    function loadPicker() {
      gapi.load('auth', {'callback': onAuthApiLoad});
      gapi.load('picker', {'callback': onPickerApiLoad});
    }

    Picker = {
      load: loadPicker
    };

    return Picker;
});
