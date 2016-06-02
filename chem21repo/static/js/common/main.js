define(["jquery","jquery.mobile.config","uri_js/jquery.URI","jquery.mobile","jquery.colorbox","flow_chart","quiz","jquery.throttle-debounce", "popcorn"], function($) {
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
        $("aside figure.youtube a, figure.inline.youtube a, figure.inline.youtube .headers, aside figure.youtube .headers").not($(".admin_tools a"))
            .on("click", function() {
                $("#popcorn_holder").remove();
                var $fig = $(this).closest("figure");
                var $a = $fig.find("a");
                var $headers = $fig.find(".headers");
                $a.children().fadeOut();
                $headers.fadeOut();
                $a.append("<div id=\"popcorn_holder\"><div id=\"popcorn_video\"></div><div id=\"popcorn_footnote\"></div></div>");
                $popcorn_holder=$a.find("#popcorn_holder");

                var ww = $fig.width();
                var vq = "";
                if(ww>1400) {
                    ph = 1080;
                    pw = 1440;
                } else if (ww>960) {
                    ph = 720;
                    pw = 960;
                } else if (ww>640) {
                    ph = 480;
                    pw = 640;
                } else if (ww>480) {
                    ph = 360;
                    pw = 480;
                } else {
                    ph = 240;
                    pw= 320;
                }
                $popcorn_holder.height(ph);
                $popcorn_holder.find("#popcorn_video").height(ph);

                //$(this).uri().setSearch("vq", vq);
                var pop = Popcorn.smart(
                   '#popcorn_video',
                   $a.attr("href") );

                 /* add a footnote at 2 seconds, and remove it at 6 seconds
                 pop.footnote({
                   start: 2,
                   end: 6,
                   text: "Pop!",
                   target: "popcorn_footnote"
                });
                 
                $.colorbox({
                    iframe:true, 
                    innerWidth:"90%", 
                    innerHeight:"90%", 
                    href: $(this).attr("href")
                }); */
                return false;
        });
    });
});