define(["jquery"], function($) {
    $(function() {
        $.fn.listPositionFix = function() {
            var targets = this.find("li");
            var target_containers = this.find("ol");
            var that = this;
            var max_offset = 0;
            target_containers.css("list-style-position", "inside");
            targets.each(function() {
                $(this).wrapInner("<div class=\"jquery-list-position-fix\"></div>");
                var wrapper = $(this).children(".jquery-list-position-fix");
                wrapper.css("display", "inline");
                $(this).css("position","relative");
                var offset = wrapper.position()['left'];
                if(offset > max_offset) {
                    max_offset = offset;
                }
                $(this).append("<div class=\"clear\">&nbsp;</div>");
            });
            console.debug(max_offset);

            target_texts = targets.find(".jquery-list-position-fix");
            target_texts.css("float", "right");
            target_texts.css("display", "block");
            target_texts.each(function() {
                $(this).width($(this).closest("li").width() - max_offset + 3);

                $(this).find("ol").css("position","relative").css("left", 2*max_offset/-2);
            });
            target_text

            return this;
        };
    });
});