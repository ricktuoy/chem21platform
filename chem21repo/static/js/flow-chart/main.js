define(["jquery"], function($) {	
	$(".reaction-discovery").not("*:first").hide();

	$(".reaction-discovery .description td").hide();
	$(".reaction-discovery .outcome td").hide();
	$(".reaction-discovery .choice td").hide();

	function show_next_reaction(el) {
		var react = el.closest(".reaction-discovery");
		var tabs = react.find(".flow-chart");
		var fail = false;
		tabs.each(function() {
			var selected = $(this).find(".choice .selected");
			console.debug(selected);
			if(!selected.length || selected.hasClass("bad")) {
				fail = true;
			}
		});
		if(!fail) {
		react.nextAll(".reaction-discovery").hide();
		var next = react.nextAll(".reaction-discovery:first");

		next.show();
		$(document).scrollTop( react.offset().top ); 
		}
	}
	$(".reaction-discovery thead").click(function() {
		if(($this).hasClass("open")) {
			return;
		}
		var react = $(this).closest(".reaction-discovery");
		var $desc = react.find(".description");
		if($desc.length) {
			$desc.fadeIn(100);
		} else {
			var $choice = react.find(".choice");
			$choice.fadeIn(100);
		}
		$(this).addClass("open");
	});

	$(".reaction-discovery .description").click(function() {
		if(($this).hasClass("open")) {
			return;
		}
		var react = $(this).closest(".reaction-discovery");
		var $choice = react.find(".choice");
		$choice.fadeIn(100);
		$(this).addClass("open");
	});
	$(".reaction-discovery .choice .good").click(function() {
		var tab = $(this).closest("table");
		tab.find(".selected").removeClass("selected");
		$(this).addClass("selected");
		//TODO: deselect all other selected.
		show_next_reaction($(this));
		tab.find(".outcome td").css("visibility","hidden");
		tab.find(".outcome .success").css("visibility", "visible").fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);;
	});
	$(".reaction-discovery .choice .ok").click(function() {
		var tab = $(this).closest("table");
		tab.find(".selected").removeClass("selected");
		$(this).addClass("selected");
		show_next_reaction($(this));
		tab.find(".outcome td").css("visibility","hidden");
		tab.find(".outcome .amend").css("visibility", "visible").fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);;
	});
	$(".reaction-discovery .choice .bad").click(function() {
		var tab = $(this).closest("table");
		tab.find(".selected").removeClass("selected");
		tab.find(".outcome td").css("visibility","hidden");
		tab.find(".outcome .fail").css("visibility", "visible").fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);;
		$(this).addClass("selected");
	});

});