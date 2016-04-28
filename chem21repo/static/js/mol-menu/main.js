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
            $canvas.width(200)
            var CDcanvas = new ChemDoodle.ViewerCanvas(id);
              CDcanvas.specs.bonds_width_2D = .6;
              CDcanvas.specs.backgroundColor = undefined;
              CDcanvas.specs.bonds_saturationWidth_2D = .18;
              CDcanvas.specs.bonds_hashSpacing_2D = 2.5;
              CDcanvas.specs.atoms_font_size_2D = 10;
              CDcanvas.specs.atoms_font_families_2D = ['Helvetica', 'Arial', 'sans-serif'];
              CDcanvas.specs.atoms_displayTerminalCarbonLabels_2D = true;
              CDcanvas.emptyMessage = 'No Data Loaded!';
            molDef = JSON.parse('"'+molDef+'"');
            var molecule = ChemDoodle.readMOL(molDef);
            CDcanvas.loadMolecule(molecule);
            CDcanvas.repaint();
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
            $iv.find(".loading").remove();
            $clink.colorbox.resize();
            $(this)[0].play();
        });
    });
});