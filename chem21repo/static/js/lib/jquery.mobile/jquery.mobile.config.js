define(['jquery'], function ($) {

    $(document).on("mobileinit", function () {
        // Prevents all anchor click handling
        $.mobile.linkBindingEnabled = false;

        // Disabling this will prevent jQuery Mobile from handling hash changes
        $.mobile.hashListeningEnabled = false;

        $.mobile.ignoreContentEnabled = true;

        $.mobile.ajaxEnabled = false;
        //$.mobile.pushStateEnabled = false;
    });

});