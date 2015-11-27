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



        function getObjectRef(el) {
            var sparts = el.attr("class").match(/\brepo-object-(.+)-(\d+)\b/);
            return {'obj'=>sparts[1], 'pk'=>sparts[2]}
        }

        function getElFromObjectRef(ref) {
            return $(".sortable .li.repo-object-"+ref['obj']+"-"+ref['pk']);
        }

        function getElsFromObjectRefs(refs) {
            $($.map(refs, getElFromObjectRef)).map (function() { return this.get(0) };
        }

        function getObjectRefs(els) {
            return els.map(getObjectRef).get();
        }

        function clearDirtyFlags() {
            $(".sortable li").removeClass("dirty");
        }




        var onRelocate = function(e, ui) {
            function getAjaxUrlFromEl(el, dest) {
                var sref = getObjectRef(el);
                if ($.type(dest) == "string" && dest == "top") {
                    var to = "0";
                } else {
                    var dref = getObjectRefFromEl(dest);
                    var to = dref['pk'];
                }
                var url = "/" + sref['obj'] + "/move/" + sref['pk'] + "/" + to;
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
        $(".sortable li").addClass( "mjs-nestedSortable-brURLanch mjs-nestedSortable-collapsed" ); 
        $( ".sortable li .disclose" ).addClass( "ui-icon ui-icon-plusthick" );
        $('.disclose').on('click', function() {
            $(this).closest('li').toggleClass('mjs-nestedSortable-collapsed').toggleClass('mjs-nestedSortable-expanded');
            $(this).toggleClass('ui-icon-plusthick').toggleClass('ui-icon-minusthick');
        });

        $("#push_changes").on('click', function() {
            var dirty = $(".sortable li.dirty");
            var data = getObjectRefs(dirty);
            $.post(push_url, data).done(function(data) {
                clearDirtyFlags();
            }).fail(function(jqXHR, textStatus, errorThrown) {})
        });

        function setExpandCookie() {
            $.cookie('c21repo-expanded',JSON.stringify());
        }

        function loadExpandCookie() {
            JSON.parse();
        }

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
                        window.location = url;
                    break;
                }
            }
        });
    });
});