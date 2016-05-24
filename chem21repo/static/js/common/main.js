define(["jquery","jquery.mobile.config","uri_js/jquery.URI","jquery.mobile","jquery.colorbox","flow_chart","quiz","jquery.throttle-debounce"], function($) {
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
        $("aside figure.youtube a, figure.inline.youtube a").not($(".admin_tools a"))
            .on("click", function() {
                var ww = $(window).width();
                var vq = "";
                if(ww>1200) {
                    vq = "hd1080";
                } else if (ww>1000) {
                    vq = "hd720";
                } else if (ww>800) {
                    vq = "large";
                } else if (ww>600) {
                    vq = "medium";
                } else {
                    vq = "small";
                }
                $(this).uri().setSearch("vq", vq);

                $.colorbox({
                    iframe:true, 
                    innerWidth:"90%", 
                    innerHeight:"90%", 
                    href: $(this).attr("href")
                });
                return false;
        });
    });
});