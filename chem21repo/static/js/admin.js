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
	function show_topic_menu(topic_el)  {
		$("#front-menu li", "body.front").each(function() {
			$(this).removeClass("hover");
		});
		topic_el.addClass("hover");
		var topic = get_topic_panel(topic_el.data("topic"));
		$(".topic, .slide","body.front").hide();
		topic.show();
	}
	$("#front-menu", "body.front").on("mouseenter", "li", function(e) {
		if(!$("#front-menu").hasClass("mobile-opened"))  {  
			show_topic_menu($(this));
		}
	});
	$("#front-menu", "body.front").on("click", "li a", function(e) {
		var li = $(this).closest("li");
		var menu = $(this).closest("#front-menu");
		if(menu.hasClass("mobile-opened"))  { 
			e.preventDefault();
			e.stopImmediatePropagation();
			show_topic_menu(li);
			//menu.removeClass("mobile-opened");
			//menu.slideUp();
		}
	});
	$(".topic:visible .content ul", "body.front").on("mouseleave", function(e) {
		var menu_item = get_topic_menu_item($(this).data("topic"));
		menu_item.removeClass("hover");
		$(".topic, .slide","body.front").hide();
		$(".topic, .slide","body.front").show();
	});

	$("#menu-toggle-link").on("click", function() {
		if($("body").hasClass("front")) {
			var menu = $("#front-menu");
			if(!menu.hasClass("mobile-opened")) {
				menu.addClass("mobile-opened");
				menu.slideDown();
			} else {
				menu.removeClass("mobile-opened");
				menu.slideUp();
			}
		}
	});

});