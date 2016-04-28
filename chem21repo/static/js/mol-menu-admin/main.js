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
            var choices = ["<option value=\"-\">-----</option>"];
            $.each( data, function(k,v) {
                choices.push( "<option value=\""+v.pk+"\">"+v.name+"</option>" );
            });
            console.debug(choices);
            $("#video-menu li").each(function() {
                $(this).append($("<select />", {html: choices.join("")}));
                var val = $(this).data("molPk");
                if(!val) val="-";
                $(this).find("select").val(val);
            });
        });

        $("#video-menu li").on("change", "select", function() {
            console.debug("Molecule widget changed");
            var vidId = $(this).closest("li").data("pk");
            var molId = $(this).val();
            var url ="/set_molecule/uniquefile/" + vidId + "/" + molId + "/";
            $.post(url, function(data) {
                console.log(data);
            }, "json");

        });

    });
});