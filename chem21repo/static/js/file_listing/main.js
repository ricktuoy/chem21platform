define(["jquery", "jquery.colorbox", ], function($) {
    //the jquery.alpha.js and jquery.beta.js plugins have been loaded.
    $(function() {
        $(".file_type_video").colorbox({onComplete : function() {$(this).colorbox.resize()} }  );
    });
});