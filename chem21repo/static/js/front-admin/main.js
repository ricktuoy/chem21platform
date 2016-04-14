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
        var otype = $("#learning_reference_type").val();
        var opk = $("#learning_reference_pk").val();
        var url = '/upload_media/'+otype+'/'+opk;
        $('#media_upload .fileupload').fileupload({
            url: url,
            dataType: 'json',
            done: function (e, data) {
                $.each(data.result, function (index, file) {
                    var para = $('<a />').attr("href",file.url).text(file.name);
                    para.wrap($("<li />"));
                    para.appendTo('#media_upload .files');
                });
            },
            progressall: function (e, data) {
                $("#media_upload .progress, #media_upload .files").show();
                var progress = parseInt(data.loaded / data.total * 100, 10);
                $("#media_upload .progress-bar-success").width(progress+"%");
            }
        }).prop('disabled', !$.support.fileInput)
            .parent().addClass($.support.fileInput ? undefined : 'disabled');

        
    });
});