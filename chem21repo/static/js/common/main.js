define(["jquery","jquery.colorbox","list_fix","quiz"], function($) {
    $(function() {
        $("#class_nav").listPositionFix();
        $("aside figure a, figure.inline a").colorbox({
            onComplete: function() {
                $(this).colorbox.resize();
            }
        });
    });
});