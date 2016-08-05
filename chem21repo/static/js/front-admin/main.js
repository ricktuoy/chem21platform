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

        $('input.fileupload').fileupload({
            url: undefined, // use form action
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
                $(this).closest(".fileupload_wrapper").find(".progress, .files").show();
                var progress = parseInt(data.loaded / data.total * 100, 10);
                $(this).closest(".fileupload_wrapper").find(".progress-bar-success").width(progress+"%");
            }
        });

        $('#djDebug').on('mouseover', 'a', function() {
            $(this).removeClass('ui-link');
        });

    });
});