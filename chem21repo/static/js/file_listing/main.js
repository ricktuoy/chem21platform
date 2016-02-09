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
        $(".file_type_video").colorbox({
            onComplete: function() {
                $(this).colorbox.resize()
            }
        });
        if($("#lessons_tree").data("permStructure")) {
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
        }

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
                    }).get()),{ path: '/' });
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


        $("#sources_tree").contextmenu({
            delegate: "li",
            menu: [
                {title: "Edit", cmd: "Edit", uiIcon: "ui-icon-edit"},
            ],
            select: function(event, ui) {
                switch(ui.cmd) {
                    case "Edit":
                    case "New":
                        var url = ui.target.closest("li").data("url"+ui.cmd);
                        var from_url = ui.target.closest("li").data("fromUrl"+ui.cmd);
                        var return_on_save = {url: window.location.pathname, fromUrl:from_url}
                        $.cookie("admin_save_redirect", JSON.stringify(return_on_save),{ path: '/' });
                        window.location = url;
                        break;
                }
            }
        })
        var commands = [{title: "Edit", cmd: "Edit", uiIcon: "ui-icon-edit"},
                {title: "View changes", cmd:"Changes", uiIcon: "ui-icon-save"}];
        if($("#lessons_tree").data("permStructure")) {
            commands = commands.concat( [
                {title: "Create new ...", cmd: "New", uiIcon: "ui-icon-new"},
                {title: "Add selected sources", cmd: "Add files", uiIcon: "ui-icon-new"},
                {title: "Remove", cmd: "Remove", uiIcon: "ui-icon-delete"},
                {title: "Delete", cmd: "Delete", uiIcon: "ui-icon-delete"}
            ] );
        }
        if($("#lessons_tree").data("permPublish")) {
            commands = commands.concat( [
                {title: "Show dirty data", cmd: "Dirty", uiIcon: "ui-icon-delete"},
                {title: "Detach", cmd: "Detach", uiIcon: "ui-icon-detach"},
                {title: "Push", cmd: "Push", uiIcon: "ui-icon-save"}
            ] );
        }
        $("#lessons_tree").contextmenu({
            delegate: "li",
            menu: commands,               
            select: function(event, ui) {
                switch(ui.cmd) {
                    case "Edit":
                    case "New":
                        var url = ui.target.closest("li").data("url"+ui.cmd);
                        var from_url = ui.target.closest("li").data("fromUrl"+ui.cmd);
                        var return_on_save = {url: window.location.pathname, fromUrl:from_url}
                        $.cookie("admin_save_redirect", JSON.stringify(return_on_save), { path: '/' });
                        window.location = url;
                        break;
                    case "Add files":
                        var el = ui.target.closest("li");
                        var url = el.data("urlAddFiles");
                        $.post(url, {'refs':getObjectRefs($("#sources_tree li.selected"))}, function(data) {
                            location.reload();
                        });
                        break;
                    case "Remove":
                        var url = ui.target.closest("li").data("urlRemove");
                        $.get(url, function(data) { 
                            el = getElFromObjectRef($("#lessons_tree"),data['success']); 
                            el.remove();
                        }).fail(function() 
                            {alert("FAIL");
                        });
                        break;
                    case "Delete":
                        var url = ui.target.closest("li").data("urlDelete");
                        $.get(url, function(data) { 
                            el = getElFromObjectRef($("#lessons_tree"),data['success']); 
                            el.remove();
                        }).fail(function() 
                            {alert("FAIL");
                        });
                        break;
                    case "Dirty":
                        var el = ui.target.closest("li");
                        var ref = getObjectRef(el);
                        $.get("/dirty/"+ref.obj+"/"+ref.pk+"/", function(data) {
                            alert(JSON.stringify(data));
                        })
                        break;
                    case 'Push':
                        $.post('/push/', {'refs':[getObjectRef(ui.target.closest("li")),]}, function(data) {
                            console.debug(data);
                        });
                        break;
                    case "Detach":
                        $.post('/local/strip_remote/', {'refs':[getObjectRef(ui.target.closest("li")),]}, function(data) {
                            console.debug(data);
                        });
                        break;
                    case "Changes":
                        console.debug("Changes");
                        var el = ui.target.closest("li");
                        var url = el.data("changesUrl");
                        //console.debug(url);
                        window.location = url;
                        break;
                }
            }
        });

        $("#lessons_tree li").on("click", function(event) {
            if($(event.target).closest("li")[0]==this && !$(event.target).hasClass("disclose")) {
                if(!event.ctrlKey) {
                    $("#lessons_tree li").removeClass("selected");
                    $(this).addClass("selected");
                } else {
                    $(this).toggleClass("selected");
                }
                event.preventDefault();
            }
        });
        $("#sources_tree li").on("click", function(event) {
            if($(event.target).closest("li")[0]==this && !$(event.target).hasClass("disclose")) {
                var ref = getObjectRef($(this));
                if(ref.obj=="source_file" || ref.obj=="cut_file") {
                    if(!event.ctrlKey) {
                        $("#sources_tree li").removeClass("selected");
                        $(this).addClass("selected");
                    } else {
                        $(this).toggleClass("selected");
                    }
                    event.preventDefault();
                }
            }
        });

        $("#remote-sync").on("submit", function(event) {
            var push_url = "/push/"
            var new_data = getObjectRefs($("#lessons_tree .new"));
            var update_data = getObjectRefs($("#lessons_tree .dirty"));
            $.post(push_url, {'refs':new_data}).done(function(data) {
                clearDirtyFlags();
                 $.post(push_url, {'refs':update_data}).done(function(data) {
                clearDirtyFlags();
            }).fail(function(jqXHR, textStatus, errorThrown) {});
            }).fail(function(jqXHR, textStatus, errorThrown) {});
           
            event.preventDefault();
        });

        $("#local-ops").on("submit", function(event) {
            event.preventDefault();
            var action = $(this).find("select[name=action] option:selected").val();
            var callbacks = {
                clear: {
                    succeed: function(data) {
                        els = getElsFromObjectRefs($("#lessons_tree"),data['result']);
                        els.removeClass("dirty");
                    },
                    fail: function(jqXHR, textStatus, errorThrown) {
                        els = getElsFromObjectRefs($("#lessons_tree"),data['result']);
                        els.removeClass("dirty");
                    } 
                },
                sync: {
                    succeed: function(data) {
                        location.reload();
                    },
                    fail: function(data) {
                        location.reload();
                    }
                },
                strip_remote: {
                    succeed: function(data) {
                        location.reload();
                    },
                    fail: function(data) {
                        location.reload();
                    }
                }
            }
            if (!action || action=="_") {
                $("#lessons_tree li").addClass("selected");
            } else {
                var url = "/local/"+action+"/";
                var data = getObjectRefs($("#lessons_tree li.selected"));
                var action_succeed = callbacks[action]['succeed'];
                var action_fail = callbacks[action]['error'];
                $.post(url, {'refs':data}, action_succeed).fail(action_fail);
            }
        }); 
        $('#fileupload').fileupload({
            dataType: 'json',
            done: function (e, data) {
                $.each(data.result.files, function (index, file) {
                    $('<p/>').text(file.name).appendTo(document.body);
                });
            }
        });

        var cache = {};
        $( "#biblio" ).autocomplete({
            minLength: 2,
            source: function( request, response ) {
                var term = request.term;
                if ( term in cache ) {
                    response( cache[ term ] );
                    return;
                }
         
                $.getJSON( "endnote/search/"+request.term+"/", function( data, status, xhr ) {
                    cache[ term ] = data;
                    response( data );
                });
            }
        });
    });
});