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
                num);
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

        $("#publish_progress").progressbar({"value": false}).hide();

        var publish = function(source_data, publish_url, type, progress, label, chunk_size) {
            var data = source_data.slice(0);
            var initial_length = data.length;
            var published_paths = [];
            var num_succeeded = 0;

            var all_returned = [];
            var promise = $.Deferred();
            var post_defaults = function() { return {'publish_format': type} };
            progress.progressbar( "option", "max", initial_length);

            var format_data_fn =  function(out) {
                return function(i, el) {
                    var k = el['name'];
                    var v = el['value'];
                    if(k == "csrfmiddlewaretoken") {
                        return;
                    }
                    if(!(k in out)) {
                        out[k] = [v];
                    } else {
                        out[k].push(v);
                    }
                };
            };

            label.text("Publishing changed " + type + " content");
            if (typeof chunk_size === 'undefined') {
                progress.progressbar( "option", "value", false );
                var out = post_defaults();
                $.each(data, format_data_fn(out));

                $.post(publish_url, out,
                    function( ret ) {
                        all_returned.push(ret);
                        promise.resolve(all_returned);
                        progress.progressbar("option", "value", initial_length);
                        label.text("Complete.");
                    }
                );
            } else {
                // initialise progress bar
                var chunks = [];
                while(data.length) {
                    var chunk = data.splice(0, chunk_size);
                    chunks.push(chunk);
                    var out = post_defaults();
                    $.each(chunk, format_data_fn(out));
                    $.post(publish_url, out, 
                        function( ret ) {
                            all_returned.push(ret);
                            num_succeeded += ret.num_succeeded;
                            progress.progressbar("value", num_succeeded);
                            label.text("Publishing "+type+", "+data.length+" objects remaining.");
                            if(data.length == 0 && all_returned.length == chunks.length) {
                                label.text("Complete.");
                                promise.resolve(all_returned);
                            }
                        }
                    );
                }
            }
            return promise;
        }

        var init_publish = function(data, pdf_url) {
            var progress = $("#publish_progress");
            var label = progress.find(".progress-label");
            progress.show();
            console.debug(pdf_url);
            var pdf_ids = $.post(pdf_url, data);
            var html_promise = publish(data, window.location.pathname, "html", progress, label, 5);
            $.when(html_promise, pdf_ids).done(
                function(html_r, pdf_r) {
                    var pdf_data = pdf_r[0];
                    var pdf_promise = publish(pdf_data.objects, window.location.pathname, "pdf", progress, label, 1);
                    $.when(pdf_promise).done(function(pdf_ret_data) {
                        var scorm_promise = publish(data, window.location.pathname, "scorm", progress, label);
                        $.when(scorm_promise).done(function(scorm_data) {
                            //window.location.reload();
                        });   
                    });
                }
            );
        };

        $("form#publish_changed").on("submit", function(e) {
            e.preventDefault();
            var form_data = $(this).serializeArray();
            var pdf_url = $(this).data("pdfIdsUrl");
            init_publish(form_data, pdf_url);
        });

        $("form#publish_all").on("submit", function(e) {
            e.preventDefault();
            var progress = $("#publish_progress");
            var label = progress.find(".progress-label");
            var pdf_url = $(this).data("pdfIdsUrl");
            progress.show();
            $.get($(this).data("publishableIdsUrl"), function( data ) {
                init_publish(data.objects, pdf_url);
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