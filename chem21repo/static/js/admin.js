$(document).ready(function() {	
	$("a.admin-edit").on("click", function(event) {
		var from_url = $(this).data("fromUrlEdit");
		var return_on_save = {url: window.location.pathname, fromUrl:from_url};
    	$.cookie("admin_save_redirect", JSON.stringify(return_on_save), { path: '/' });
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
	function show_topic_menu(topic_el) {
		$("#front-menu li", "body.front").each(function() {
			$(this).removeClass("hover");
		});
		topic_el.addClass("hover");
		var topic = get_topic_panel(topic_el.data("topic"));
		$(".topic, .slide","body.front").hide();
		topic.show();
		$("#front-back","body.front").fadeIn();
	}
	$("#front-menu", "body.front").on("mouseenter", "li", function(e) {
		if(!$("#front-menu").hasClass("mobile-opened"))  {  
			show_topic_menu($(this));
		}
	});
	$("#front-menu", "body.front").on("click", "li a", function(e) {
		var li = $(this).closest("li");
		var menu = $(this).closest("#front-menu");
		if(menu.hasClass("mobile-opened")) { 
			e.preventDefault();
			e.stopImmediatePropagation();
			show_topic_menu(li);
		}
	});

	$("#menu-toggle-link").on("click", function(e) {
		e.preventDefault();
		e.stopImmediatePropagation();
		if($("body").hasClass("front")) {
			var menu = $("#front-menu");
			if(!menu.hasClass("mobile-opened")) {
				menu.addClass("mobile-opened");
				menu.slideDown();
			} else {
				menu.removeClass("mobile-opened");
				menu.slideUp();
			}
		} else {
			var nav = $("#class_nav");
			if(!nav.hasClass("mobile-opened")) {
				nav.addClass("mobile-opened");
				nav.slideDown();
			} else {
				nav.removeClass("mobile-opened");
				nav.slideUp();
			}

		}
	});

	$("body.front").on("click","#front-back",function(e) {
		$(this).fadeOut("fast");
		$("#front-menu li", "body.front").each(function() {
			$(this).removeClass("hover");
		});
		$(".topic","body.front").hide();
		$(".slide","body.front").show();
		if($("#front-menu").hasClass("mobile-opened"))  {
			$("#front-menu").slideUp();
			$("#front-menu").removeClass("mobile-opened");
		}
	});
	
	$("figure.presentation video").on("play",function(e) {
		$(this).closest("figure.presentation").find("figcaption.overlay").slideUp();
	});
	$("figure.presentation video").on("pause", function(e) {
		$(this).closest("figure.presentation").find("figcaption.overlay").slideDown();
	});

	$("figure.presentation video").on("ended", function(e) {
		$(this).closest("figure.presentation").find("figcaption.overlay").slideDown();
	});
});