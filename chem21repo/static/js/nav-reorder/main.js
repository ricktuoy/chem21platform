define(["jquery", "jquery.colorbox", "jquery.mjs.nestedSortable", "jquery.cookie", "jquery.ui-contextmenu", "jquery.fileupload", "jquery-ui/autocomplete"], function($) {
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

        function getObjectRef(el) {
            return {'obj':el.data("loType"), 'pk':el.data("loPk")};
        }

        function getElFromObjectRef(dest,ref) {
            return dest.find("li[lo-type='"+ref['obj']+"'][lo-pk='"+ref['pl']+"']");
        }

        function getElsFromObjectRefs(dest, refs) {
            out =  $($.map(refs, function(el) { return getElFromObjectRef(dest, el); })).map (function() { return this.get(0) });
            return out;
        }

        function getObjectRefs(els) {
            return els.map(function(){ return getObjectRef($(this))}).get();
        }

        var onRelocate = function(e, ui) {
            function getAjaxUrlFromEl(el, dest) {
                var sref = getObjectRef(el);
                if ($.type(dest) == "string" && dest == "top") {
                    var to = "0";
                } else {
                    var dref = getObjectRef(dest);
                    var to = dref['pk'];
                }
                var url = "/" + sref['obj'] + "/move/" + sref['pk'] + "/" + to;
                if (sref['obj'] == "lesson" || sref['obj'] == "question") {
                    pref = getObjectRef(el.parent().closest("li"));
                    url += "/" +pref['pk']
                }
                return url;
            }
            var movedEl = $(ui.item);
            var allEls = movedEl.closest("ol").children("li");
            var newPos = allEls.index(movedEl) + 1;
            if (newPos > 1) {
                var destEl = $(allEls.get(newPos - 2));
                var url = getAjaxUrlFromEl(movedEl, destEl);
            } else {
                var url = getAjaxUrlFromEl(movedEl, "top")
            }
            $.get(url).done(function(data) {
            }).fail(function(jqXHR, textStatus, errorThrown) {});
        };

        var set_sortable = function() {
            var ns = $('#class_nav ol').first().nestedSortable({
                forcePlaceholderSize: true,
                handle: 'a',
                items: 'li',
                toleranceElement: '> a',
                opacity: .6,
                placeholder: 'placeholder',
                revert: 250,
                tabSize: 25,
                maxLevels: 5,
                expandOnHover: null,
                isAllowed: isDropAllowed,
                startCollapsed: true,
                relocate: onRelocate,
                disableParentChange: true,
                protectRoot: true
            });
        };


        set_sortable();
       

        $( ".sortable" ).addClass( "ui-sortable mjs-nestedSortable-branch" );
        $( ".sortable li" ).addClass( "mjs-nestedSortable-branch" ); 

    });
});