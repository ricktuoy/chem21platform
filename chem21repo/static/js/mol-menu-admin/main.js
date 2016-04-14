define(["jquery","jquery.fileupload", "mol_menu", "front_admin"], function($) {
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
        var mol_url = "/get_molecules/";
        $.getJSON(mol_url, function(data) {
            var choices = ["<option value="-">-----</option>"];
            $.each( data.molecules, function(k,v) {
                choices.push( "<label>Choose molecule:</label><option value=\""+v.pk+"\">"+v.name+"</option>" );
            });
            $("#video-menu li").each(function() {
                $(this).append($("<select />", {html: choices.join("")}));
            });
        });

        $("#video-menu li select").on("change", function() {
            var vidId = $(this).closest("li").data("pk");
            var molId = $(this).val();
            var url ="/set_molecule/uniquefile/" + vidId + "/" + molId;
            $.getJSON(url, function(data) {
                console.log(data);
            });

        });

    });
});