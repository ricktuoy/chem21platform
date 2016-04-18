define(["jquery","jquery.colorbox","common"], function($) {
    $(function() {
        var $iv = $("#inlinevideocontent");
        var $ivv = $("#inlinevideocontent video"); 
        $(".figure-menu canvas.molecule").each(function() {
            var $canvas = $(this);
            var molDef = $canvas.data("molDef");
            var molName = $canvas.data("name");
            var height = $canvas.width() * 0.8;
            var id = "molecule_"+molName;
            $canvas.attr("id",id);
            $canvas.height(height);
            var CDcanvas = new ChemDoodle.ViewerCanvas(id);
            var molecule = ChemDoodle.readMOL(molDef);
            CDcanvas.loadMolecule(molecule);
        });
        $("#video-menu a[data-video-type='html5']").colorbox({
            inline: true,
            width: "85%",
            onOpen: function() {
                var url = $(this).attr("href");
                $(this).data('url', url);
                $ivv.hide();
                $iv.append($("<p class=\"loading\">Loading video ...</p>"));
                $ivv.attr("src",url);
                $ivv[0].load();
                $ivv.data("colorbox-link", $(this));
                $(this).attr("href", "#inlinevideocontent");
            },
            onCleanup: function() {
                var url = $(this).data('url');
                $ivv.attr("src","");
                $(this).attr("href", url);
            },
            onComplete: function() {
                $(this).colorbox.resize();
            }
        });
        $("#inlinevideocontent video").on("loadeddata", function() {
            var $clink = $(this).data("colorbox-link");
            $(this).show();
            $(iv).find(".loading").remove();
            $clink.colorbox.resize();
            $(this)[0].play();
        });
    });
});