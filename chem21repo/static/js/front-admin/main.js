define(["google_picker","jquery","jquery.fileupload","jquery-ui/progressbar","nav_reorder","common"], function(GPicker, $) {
    String.prototype.format = function () {
      var args = arguments;
      return this.replace(/\{(\d+)\}/g, function (m, n) { return args[n]; });
    };
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
        $(".progress, .files").hide();
        $(".progress").width("100%");

        $("#site-header").on("click", "#import_references_trigger", function(e) {
            e.preventDefault();
            $(this).hide();
            $(this).next(".fileupload_wrapper").fadeIn();
        });
        $('input.fileupload').fileupload({
            dataType: 'json',
            done: function (e, data) {
                var that=this;
                $.each(data.result, function (index, file) {
                    var para = $('<a />').attr("href",file.url).text(file.name);
                    para.wrap($("<li />"));
                    $(that).closest(".fileupload_wrapper").find('.files').append(para);
                    $(that).closest(".fileupload_wrapper").find(".progress").hide();
                });
            },
            progressall: function (e, data) {
                var that=this;
                $(that).closest(".fileupload_wrapper").find(".progress, .files").show();
                var progress = parseInt(data.loaded / data.total * 100, 10);
                $(that).closest(".fileupload_wrapper").find(".progress-bar-success").width(progress+"%");
            }
        });

        $("#site-header").on("fileuploaddone", "#import_references", function(e, data) {
            var that=this;
            var html = $("<ul></ul>").addClass("messages");
            $.each(data.result, function (index, file) {
                var mod = file.modified.length;
                var cre = file.created.length;
                var message = 'Processed file {0}: created {1} references and modified {2}.'.format(
                    file.name, cre, mod);
                var message_html = $("<li></li>").text(message).addClass("success");
                html.append(message_html);
            });
            $("#admin_tools").before(html);
        });

        $("#content").on("fileuploaddone", "#upload_json", function(e, data) {
            window.location.reload();
        });

        $("a.delete-figure").on("click", function(e) {
            e.stopPropagation();
            e.preventDefault();
            var num = $(this).data("figNum");
            var url = "/figure/delete/{0}/{1}/{2}".format(
                $("#learning_reference_type").val(), 
                $("#learning_reference_pk").val(), 
                num)
            $.getJSON(url, function() {
                window.location.reload(true);
            });
        });

        $(".presentation a.delete").on("click", function(e) {
            e.stopPropagation();
            e.preventDefault();
            var url = $(this).attr("href");
            $.getJSON(url, function() {
                window.location.reload(true);
            });
        });

        var publish_pages = function(data, progress) {
            var initial_length = data.length;
            console.debug("initial_length: "+initial_length);
            var published_paths = [];
            var num_succeeded = 0
            // initialise progress bar
            progress.progressbar({"value": 0, "max": initial_length});
            while(data.length) {
                var chunk = data.splice(0,10);
                var out = {};
                $.each(chunk, 
                    function(i, el) {
                        var k = el['name'];
                        var v = el['value'];
                        console.debug(k);
                        if(k == "csrfmiddlewaretoken") {
                            return;
                        }
                        if(!(k in out)) {
                            out[k] = [v];
                        } else {
                            out[k].push(v);
                        }
                    }
                );
                $.post(window.location.pathname, out, 
                    function( ret ) {
                        num_succeeded += ret.num_succeeded
                        num_failed += ret.num_failed
                        console.debug(num_succeeded+" / "+initial_length)
                        progress.progressbar("value", num_succeeded);

                        //if(num_succeeded >= )
                    }
                );
            }
        }

        $("form#publish_changed").on("submit", function(e) {
            e.preventDefault();
            var data = $(this).serializeArray();
            var progress = $("#publish_progress");
            publish_pages(data, progress);
        });

        $("form#publish_all").on("submit", function(e) {
            e.preventDefault();
            console.debug($(this).data("changedIdsUrl"));
            $.get($(this).data("publishableIdsUrl"), function( data ) {
                var progress = $("#publish_progress");
                publish_pages(data.objects, progress);
            });

        });


        $('#djDebug').on('mouseover', 'a', function() {
            $(this).removeClass('ui-link');
        });

    });
    return {
        Picker:GPicker
    }
});