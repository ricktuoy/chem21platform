define(["jquery", "jquery.colorbox", "jquery.mjs.nestedSortable", "jquery.cookie", "jquery.ui-contextmenu"], function($) {
    $(function() {
        var csrftoken = $.cookie('csrftoken');

        function csrfSafeMethod(method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
        var isDropAllowed = function(placeholder, placeholderParent, currentItem) {
            return true;
        }

        var onRelocate = function(e) {
            function getAjaxUrlFromEl(el, dest) {

                var sparts = el.attr("class").match(/\brepo-object-(.+)-(\d+)\b/);

                if ($.type(dest) == "string" && dest == "top") {
                    var to = "0";
                } else {
                    var dparts = dest.attr("class").match(/\brepo-object-(.+)-(\d+)\b/);
                    var to = dparts[2];
                }
                var url = "/" + sparts[1] + "/move/" + sparts[2] + "/" + to;
                return url;
            }

            var movedEl = $(e.toElement).closest("li");
  
            var allEls = movedEl.closest("ol").children("li");
            var newPos = allEls.index(movedEl) + 1;
            if (newPos > 1) {
                var destEl = $(allEls.get(newPos - 2));
                var url = getAjaxUrlFromEl(movedEl, destEl);
            } else {
                var url = getAjaxUrlFromEl(movedEl, "top")
            }
            $.get(url).done(function(data) {
                console.log("Success");
                console.log(data);
            }).fail(function(jqXHR, textStatus, errorThrown) {});
        };
        $(".file_type_video").colorbox({
            onComplete: function() {
                $(this).colorbox.resize()
            }
        });
        var ns = $('ol.sortable').nestedSortable({
            forcePlaceholderSize: true,
            handle: 'div',
            items: 'li',
            toleranceElement: '> div',
            opacity: .6,
            placeholder: 'placeholder',
            revert: 250,
            tabSize: 25,
            maxLevels: 5,
            isTree: true,
            expandOnHover: null,
            isAllowed: isDropAllowed,
            startCollapsed: true,
            relocate: onRelocate,
            disableParentChange: true,
            protectRoot: true,

        });
        $( ".sortable" ).addClass( "ui-sortable mjs-nestedSortable-branch mjs-nestedSortable-expanded" );
        $(".sortable li").addClass( "mjs-nestedSortable-branch mjs-nestedSortable-collapsed" ); 
        $( ".sortable li .disclose" ).addClass( "ui-icon ui-icon-plusthick" );
        $('.disclose').on('click', function() {
            $(this).closest('li').toggleClass('mjs-nestedSortable-collapsed').toggleClass('mjs-nestedSortable-expanded');
            $(this).toggleClass('ui-icon-plusthick').toggleClass('ui-icon-minusthick');
        });


        $("#lessons_tree").contextmenu({
            delegate: "li",
            menu: [
                {title: "Edit", cmd: "Edit", uiIcon: "ui-icon-edit"},
                {title: "Create new ...", cmd: "New", uiIcon: "ui-icon-new"}
            ],
            select: function(event, ui) {
                switch(ui.cmd) {
                    case "Edit":
                    case "New":
                        var url = ui.target.closest("li").data("url"+ui.cmd);
                        var from_url = ui.target.closest("li").data("fromUrl"+ui.cmd);
                        var return_on_save = {url: window.location.pathname, fromUrl:from_url}
                        $.cookie("admin_save_redirect", JSON.stringify(return_on_save));
                        console.log(return_on_save)
                        window.location = url;
                    break;
                }
            }
        });
    });
});