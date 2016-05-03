define(["jquery","jquery.colorbox","common"], function($) {
    $(function() {
        var $iv = $("#inlinevideocontent");
        var $ivv = $("#inlinevideocontent video"); 
        var max_h = 0;
        $(".figure-menu canvas.molecule").each(function() {
            var $canvas = $(this);
            var molDef = $canvas.data("molDef");
            var molName = $canvas.data("name");
            
            var id = "molecule_"+molName;
            $canvas.attr("id",id);
            molDef = JSON.parse('"'+molDef+'"');
            molDef = molDef.replace(/\n\n/gm,'\n');
            var molecule = ChemDoodle.readMOL(molDef);
            var CDcanvas = new ChemDoodle.ViewerCanvas(id, 150, 150);
            CDcanvas.specs.bonds_width_2D = .6;
            CDcanvas.specs.bonds_saturationWidth_2D = .18;
            CDcanvas.specs.bonds_hashSpacing_2D = 2.5;
            CDcanvas.specs.atoms_font_size_2D = 10;
            CDcanvas.specs.atoms_font_families_2D = ['Helvetica', 'Arial', 'sans-serif'];
            CDcanvas.specs.atoms_displayTerminalCarbonLabels_2D = true;
            CDcanvas.loadMolecule(molecule, 1);
            var h = $canvas.closest("figure").height();
            var w = $canvas.closest("figure").width();
            var lh = $canvas.closest("li").height();
            CDcanvas.resize(w, h);  
            if(h>max_h) {
                max_h = h;
            }         
        });
        $(".figure-menu canvas").each(function() {
            var $canvas = $(this);
            var $fig = $canvas.closest("figure");
            var $li = $canvas.closest("li");
            var diff = max_h - $li.height() + 30;
            $li.css("margin-bottom", diff+"px");
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