$(document).ready(function() {	
	$("a.admin-edit").on("click", function(event) {
		var from_url = $(this).data("fromUrlEdit");
		var return_on_save = {url: window.location.pathname, fromUrl:from_url};
    	$.cookie("admin_save_redirect", JSON.stringify(return_on_save), { path: '/' });
    	//console.debug(return_on_save);
    	window.location = url;
    	return false;
	});
	$("a.embed").gdocsViewer({width: "100%", height: 500});
	$("a.embed").hide();
	function get_topic_panel(topic) {
		return $(".topic[data-topic=\""+topic+"\"]", "body.front");
	}
	function get_topic_menu_item(topic) {
		return $("#front-menu li[data-topic=\""+topic+"\"]", "body.front");
	}

	$("#front-menu li", "body.front").on("mouseenter", function(e) {
		$("#front-menu li", "body.front").each(function() {
			$(this).removeClass("hover");
		});
		$(this).addClass("hover");
		var topic = get_topic_panel($(this).data("topic"));
		$(".topic, .slide","body.front").hide();
		topic.show();
	});
	$(".topic:visible .content ul", "body.front").on("mouseleave", function(e) {
		var menu_item = get_topic_menu_item($(this).data("topic"));
		menu_item.removeClass("hover");
		$(".topic, .slide","body.front").hide();
		$(".topic, .slide","body.front").show();
	});

});