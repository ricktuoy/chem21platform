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


        $("aside figure.youtube, figure.inline.youtube").each(function() {
            var $fig = $(this).closest("figure");
            var $a = $fig.find("a.youtube");
            var $replace = $a.children("img");
            $a.append("<div id=\"popcorn_holder\"><div id=\"popcorn_video\"></div><div id=\"popcorn_footnote\"></div></div>");

            var $popcorn_holder = $a.find( "#popcorn_holder" );
            
            var $vid = $popcorn_holder.find( "#popcorn_video" );
            $vid.height( ($vid.width() / 4) * 3 );
            var $loader = $fig.find(".loader");
            var wrapper = Popcorn.HTMLYouTubeVideoElement('#popcorn_video');
            wrapper.src = $a.attr("href") ;
            var pop = Popcorn(wrapper);
            pop.on("playing", function(evt) {
                $loader.hide();
            });
            pop.on("ended", function(evt) {
                console.log("Ended.");
                var $popcorn_holder = $a.find( "#popcorn_holder" );
                var $disclaimer = $fig.find(".disclaimer");
                $fig.find(".action_overlay.repeat").fadeIn();
                $popcorn_holder.hide();
                $replace.fadeIn();
                $disclaimer.fadeIn();
            });
            $popcorn_holder.hide();
            $popcorn_holder.data("popcorn-object", pop);
        });
        $("aside figure.youtube, figure.inline.youtube")
            .on("click",".action_overlay", function() {
                var $fig = $(this).closest("figure");
                var $a = $fig.find("a.youtube");
                var $replace = $a.children("img");
                var $headers = $fig.find(".headers:visible");
                var $disclaimer = $fig.find(".disclaimer:visible");
                var $loader = $fig.find(".loader");
                var show_loader = function() {
                    console.log("Show loader callback");
                    $loader.show();
                var play = function() {
                    console.log("Play callback");
                    var $popcorn_holder = $a.find( "#popcorn_holder" );

                    var $loader = $fig.find(".loader");
                    $popcorn_holder.show();
                    var pop = $popcorn_holder.data("popcorn-object");
                    $loader.fadeOut();
                    $replace.hide();
                    console.log(pop);
                    pop.play();
                    $fig.find(".action_overlay").fadeOut();
                    console.log("End play callback");
                };
                $headers.fadeOut(play);
                $disclaimer.fadeOut(play);
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
