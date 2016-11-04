define(["jquery","jquery.mobile.config","jquery.math","uri_js/jquery.URI","jquery.colorbox","flow_chart","quiz","guide","jquery.throttle-debounce", "popcorn", "glossary"], function($) {
    $.fn.extend({
        scrollRight: function (val) {
            if (val === undefined) {
                return this[0].scrollWidth - (this[0].scrollLeft + this[0].clientWidth) + 1;
            }
            return this.scrollLeft(this[0].scrollWidth - this[0].clientWidth - val);
        }
    });
    $(function() {

        var table_shadows_update = function($table) {
            var $leftsh = $table.data("ui-responsive-left-shadow");
            var $rightsh = $table.data("ui-responsive-right-shadow");
            if($table.scrollLeft() == 0) {
                $leftsh.hide();
            } else {
                $leftsh.show();
            }
            if($table.scrollRight() < 5) {
                $rightsh.hide();
            } else {
                $rightsh.show();
            }
        };

        var generate_responsive_table_shadows_cb = function() {
            var $this = $(this);
            var $wrap = $("<div />").addClass("ui-responsive-wrap");
            var $leftsh = $("<div />").addClass("left-shadow");
            var $rightsh = $("<div />").addClass("right-shadow");
            var $shadows = $leftsh.add($rightsh);
            $wrap.append($shadows);
            $this.before($wrap);
            $leftsh.after($this);
            $(this).data("ui-responsive-left-shadow", $leftsh);
            $(this).data("ui-responsive-right-shadow", $rightsh);
            table_shadows_update($this);
        }

        $("#content table.ui-responsive").each(generate_responsive_table_shadows_cb);

        $("#content table.ui-responsive").on("scroll", function() {
            table_shadows_update($(this));
        });

        $(window).on("resize", function() {
            $("#content table.ui-responsive").each(function() {
                table_shadows_update($(this))
            });
        });


        $("aside figure a, figure.inline a").not($(".admin_tools a, .youtube a")).colorbox({
        	scalePhotos: true,
        	maxWidth: "95%",
        	maxHeight: "100%",
            onComplete: function() {
                $(this).colorbox.resize();
            }
        });

        $("#site-header").on("mouseenter", "#feedback", function(event) {
            $(this).addClass("hover");
        });
        $("#site-header").on("mouseleave", "#feedback", function(event) {
            $(this).removeClass("hover");
        });

        $("#site-header").on("click", "#feedback", function(event) {
            var url = $(this).find("a").attr("href");
            var win = window.open(url, "_blank");
            win.focus();
        });


        $("div.hide_solution").each(function() {
            $(this).after("<a href=\"#\" class=\"hide_solution\">Reveal</a>");
            $(this).hide();
        });

        $("#content").on("click", "a.hide_solution", function(event) {
            var $visible = $(this).prev(":visible");
            var $hidden = $(this).prev(":hidden");

            if($visible.length)  {
                $visible.hide();
                $(this).html("Reveal");
                $(this).removeClass("shown");
            } else {
                $hidden.show();
                $(this).html("Hide");
                $(this).addClass("shown");
            }
            event.preventDefault();
            return false;
        });


        $("aside figure.youtube, figure.inline.youtube").each(function() {
            var $fig = $(this).closest("figure");
            var $a = $fig.find("a.youtube");
            var href = $a.attr("href");
            var timeline_url = $a.data("timelineSources");
            var $replace = $a.children("img");
            $a.after("<div class=\"youtube\"></div>");
            $div = $fig.find("div.youtube");
            $div.append($a.children());
            $a.remove();
            $a = $div;
            $a.append("<div id=\"popcorn_holder\"><div id=\"popcorn_video\"></div><div id=\"popcorn_footnote\"></div></div>");
            var $popcorn_holder = $a.find( "#popcorn_holder" );
            var $vid = $popcorn_holder.find( "#popcorn_video" );
            $vid.height( ($vid.width() / 4) * 3 );
            var $loader = $fig.find(".loader");
            var pop = Popcorn.smart('#popcorn_video', href);
            var parsedCallback = function () {
            }  
            pop.parseJSON(timeline_url, parsedCallback);
            $popcorn_holder.find("video").prop("controls", true);
            pop.on("playing", function(evt) {
                $loader.hide();
            });
            pop.on("ended", function(evt) {
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
                var $a = $fig.find(".youtube");
                var $replace = $a.children("img");
                var $headers = $fig.find(".headers:visible");
                var $disclaimer = $fig.find(".disclaimer:visible");
                var $loader = $fig.find(".loader");
                var play = function() {
                    var $popcorn_holder = $a.find( "#popcorn_holder" );
                    var $loader = $fig.find(".loader");
                    $popcorn_holder.show();
                    var pop = $popcorn_holder.data("popcorn-object");
                    $loader.fadeOut();
                    $replace.hide();
                    pop.currentTime(0);
                    pop.play();
                    $fig.find(".action_overlay").fadeOut();
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
