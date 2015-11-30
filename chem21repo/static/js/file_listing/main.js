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
            return {'obj':sparts[1], 'pk':sparts[2]}
        }

        function getElFromObjectRef(dest,ref) {
            return dest.find("li.repo-object-"+ref['obj']+"-"+ref['pk']);
        }

        function getElsFromObjectRefs(dest, refs) {

            out =  $($.map(refs, function(el) { return getElFromObjectRef(dest, el); })).map (function() { return this.get(0) });

            return out;

        }

        function getObjectRefs(els) {
            return els.map(function(){ return getObjectRef($(this))}).get();
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
        function toggleLiEl(el) {
            el.toggleClass('mjs-nestedSortable-collapsed').toggleClass('mjs-nestedSortable-expanded');
            el.children("div").first().children(".disclose").toggleClass('ui-icon-plusthick').toggleClass('ui-icon-minusthick');
        }
        $('.disclose').on('click', function() {
            toggleLiEl($(this).closest('li'));
                setExpandCookie("c21repo-lessons-expanded", $("#lessons_tree"));
         
                setExpandCookie("c21repo-sources-expanded", $("#sources_tree"));
   
        });

        function setExpandCookie(cookie_name, dest ) {
            var dest=dest;
            $.cookie(cookie_name,JSON.stringify(
                dest.find("li.mjs-nestedSortable-expanded").map(
                    function() { 
                        return getObjectRef($(this)) 
                    }).get()));
        }

        function loadExpandCookie(cookie_name, dest) {
            var cookiedough = $.cookie(cookie_name);
            if(cookiedough) {
                var els=getElsFromObjectRefs(dest,
                    JSON.parse($.cookie(cookie_name))
                );
                els.each(function() {toggleLiEl($(this))});
            }
        }
        loadExpandCookie('c21repo-lessons-expanded', $("#lessons_tree"));
        loadExpandCookie('c21repo-sources-expanded', $("#sources_tree"));

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

        $("#remote-sync").on("submit", function() {
            var push_url = "/push/"
            var data = getObjectRefs($("#lessons_tree .dirty"));
            $.post(push_url, {'refs':data}).done(function(data) {
                clearDirtyFlags();
            }).fail(function(jqXHR, textStatus, errorThrown) {})
            return false;
        });
    });
});