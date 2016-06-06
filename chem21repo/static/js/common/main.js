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


        $("aside figure.youtube, figure.inline.youtube")
            .on("click",".action_overlay", function() {
                $("#popcorn_holder").remove();
                var $fig = $(this).closest("figure");
                var $a = $fig.find("a.youtube");
                var $replace = $a.children("img");
                var $headers = $fig.find(".headers:visible");
                var $disclaimer = $fig.find(".disclaimer:visible");
                var $loader = $fig.find(".loader");
                var show_loader = function() {
                    $loader.show();
                }
                $headers.fadeOut(show_loader);
                $disclaimer.fadeOut(show_loader);
                $a.append("<div id=\"popcorn_holder\"><div id=\"popcorn_video\"></div><div id=\"popcorn_footnote\"></div></div>");
                $popcorn_holder = $a.find( "#popcorn_holder" );
                $vid = $popcorn_holder.find( "#popcorn_video" );
                $vid.height( ($vid.width() / 4) * 3 );
                var pop = Popcorn.smart(
                       '#popcorn_video',
                       $a.attr("href") );
                pop.media.preload="none";
                $popcorn_holder.hide();
                $fig.find(".action_overlay").fadeOut();
                pop.on("playing", function(evt) {
                    $loader.fadeOut();
                    $replace.hide();
                    $loader.hide();
                    $popcorn_holder.fadeIn();
                });
                pop.on("ended", function(evt) {
                    var $disclaimer = $fig.find(".disclaimer");
                    $fig.find(".action_overlay.repeat").fadeIn();
                    $popcorn_holder.hide();
                    $replace.fadeIn();
                    $disclaimer.fadeIn();
                });
                return false;
            });
        $("aside figure.youtube, figure.inline.youtube")
            .on({"mouseenter": function() {
                    $(this).animate({"background-color":"white", "opacity": 0.6});
                },
                "mouseleave": function() {
                    $(this).animate({"background-color":"transparent", "opacity": 0.1})     
                }
            }, ".action_overlay");

    });
});