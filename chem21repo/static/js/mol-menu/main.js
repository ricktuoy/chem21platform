define(["jquery","common","chemdoodle"], function($) {
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
    });
});