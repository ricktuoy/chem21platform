define(["jquery","jquery.mobile.config","jquery.mobile","jquery.colorbox","flow_chart","quiz","jquery.throttle-debounce"], function($) {
    $(function() {
        /*
        $("#class_nav").listPositionFix();
        var resize_callback= function() {
            $("#class_nav").listPositionFix();
        };

        $(window).resize($.debounce(15, resize_callback));
        */

        $("aside figure a, figure.inline a").not($(".admin_tools a, .youtube a")).colorbox({
        	scalePhotos: true,
        	maxWidth: "95%",
        	maxHeight: "100%",
            onComplete: function() {
                $(this).colorbox.resize();
            }
        });
        $("aside figure.youtube a, figure.inline.youtube a").not($(".admin_tools a")).colorbox({
            iframe:true, innerWidth:640, innerHeight:390
        });
    });
});