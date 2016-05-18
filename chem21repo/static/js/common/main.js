define(["jquery","jquery.mobile.config","jquery.mobile","jquery.colorbox","flow_chart","quiz","jquery.throttle-debounce"], function($) {
    $(function() {
        /*
        $("#class_nav").listPositionFix();
        var resize_callback= function() {
            $("#class_nav").listPositionFix();
        };

        $(window).resize($.debounce(15, resize_callback));
        */
        console.log($.mobile === undefined && 'undefined!');
        console.log($.mobile);
        $("aside figure a, figure.inline a").not($(".admin_tools a")).colorbox({
        	scalePhotos: true,
        	maxWidth: "95%",
        	maxHeight: "100%",
            onComplete: function() {
                $(this).colorbox.resize();
            }
        });
    });
});