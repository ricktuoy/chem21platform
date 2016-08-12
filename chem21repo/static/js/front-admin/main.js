define(["jquery","jquery.fileupload","common"], function($) {
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
                console.debug("Done upload");
                console.debug(that);
                $.each(data.result, function (index, file) {
                    var para = $('<a />').attr("href",file.url).text(file.name);
                    para.wrap($("<li />"));
                    $(that).closest(".fileupload_wrapper").find('.files').append(para);
                    $(that).closest(".fileupload_wrapper").find(".progress").hide();
                });
            },
            progressall: function (e, data) {
                var that=this;
                console.debug(that);
                $(that).closest(".fileupload_wrapper").find(".progress, .files").show();
                var progress = parseInt(data.loaded / data.total * 100, 10);
                $(that).closest(".fileupload_wrapper").find(".progress-bar-success").width(progress+"%");
            }
        });

        $('#djDebug').on('mouseover', 'a', function() {
            $(this).removeClass('ui-link');
        });

    });
});