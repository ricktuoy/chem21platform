define(['jquery'], function($) {
    // The Browser API key obtained from the Google API Console.
    // Replace with your own Browser API key, or your own key.
    var ltp = $("#learning_reference_type").val();
    var lpk = $("#learning_reference_pk").val();
    //var uri = $("#google_picker_trigger").attr("href");
    return {
	    apiKey:'AIzaSyD8GRUKAHfyhqVYUJzP4YBfzqyVjva1OXY',

	    // The Client ID obtained from the Google API Console. Replace with your own Client ID.
	    clientId:"587098258526-upndrfugm9k0bn3hlj3qpqfldffktk0m.apps.googleusercontent.com",

	    // Replace with your own App ID. (Its the first number in your Client ID)
	    appId:"587098258526",

	    // Scope to use to access user's Drive items.
	    scopes:['https://www.googleapis.com/auth/drive'],

	    server_uri:"/admin/repo/question/load_gdoc/"+lpk
	}
});
