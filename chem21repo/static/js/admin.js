$(document).ready(function() {	
	$("a.admin-edit").on("click", function(event) {
		var from_url = $(this).data("fromUrlEdit");
		var return_on_save = {url: window.location.pathname, fromUrl:from_url};
    	$.cookie("admin_save_redirect", JSON.stringify(return_on_save), { path: '/' });
    	//console.debug(return_on_save);
    	window.location = url;
    	return false;
	});
});