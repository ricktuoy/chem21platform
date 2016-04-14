define(["jquery","jquery.colorbox","common"], function($) {
    $(function() {
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
        $("#video-menu a").css("border","1px solid red");
        $("#video-menu a").colorbox({
            scalePhotos: true,
            maxWidth: "95%",
            maxHeight: "100%",
            onComplete: function() {
                $(this).colorbox.resize();
            }
        });
    });
});