define(["jquery","jquery.colorbox","list_fix","quiz"], function($) {
    $(function() {
        $("#class_nav").listPositionFix();
        $("aside figure a, figure.inline a").colorbox({
        	scalePhotos: true,
        	maxWidth: "95%",
        	maxHeight: "100%",
            onComplete: function() {
                $(this).colorbox.resize();
            }
        });
    });
});