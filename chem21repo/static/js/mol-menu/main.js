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
            var CDcanvas = new ChemDoodle.RotatorCanvas3D(id, 250, 250);
            CDcanvas.specs.set3DRepresentation('Line');
            CDcanvas.specs.backgroundColor = 'black';
            CDcanvas.specs.atoms_sphereDiameter_3D = 4.0;
            CDcanvas.loadMolecule(molecule, 1);
            var h = $canvas.closest("figure").height();
            var w = $canvas.closest("figure").width();
            var lh = $canvas.closest("li").height();
            CDcanvas.resize(w, h);  
            CDcanvas.startAnimation(); 
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