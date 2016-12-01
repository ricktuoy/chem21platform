define(["jquery"], function($) {	
	$(".reaction-discovery").not("*:first").hide();
	$(".reaction-discovery .description td").hide();
	$(".reaction-discovery .outcome td").hide();
	$(".reaction-discovery tbody .outcome").hide();

	function show_next_reaction(el) {
		var react = el.closest(".reaction-discovery");
		var tabs = react.find(".flow-chart");
		var fail = false;
		tabs.each(function() {
			var selected = $(this).find(".choice .selected");
			console.log(selected);
			if(!selected.length || selected.hasClass("bad")) {
				console.log("BAD");
				fail = true;
			}
		});
		react.nextAll(".reaction-discovery").hide();
		if(!fail) {
			var next = react.nextAll(".reaction-discovery:first");
			next.show();
		} 
	};


	
	$(".reaction-discovery thead").click(function() {
		if($(this).hasClass("open")) {
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
		if($(this).hasClass("open")) {
			return;
		}
		var react = $(this).closest(".reaction-discovery");
		var $choice = react.find(".choice");
		$choice.fadeIn(100);
		$(this).addClass("open");
	});

	$(".reaction-discovery .choice td").on("click", function() {
		var tab = $(this).closest("table");
		tab.find(".outcome").show();
		tab.find(".outcome td").show();
		tab.find(".selected").removeClass("selected");
		$(this).addClass("selected");
		show_next_reaction($(this));
		tab.find(".outcome td").css("visibility","hidden");
	});

	$(".reaction-discovery .choice .good").on("click", function() {
		var tab = $(this).closest("table");
		tab.find(".outcome .success").css("visibility", "visible").fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);;
	});
	$(".reaction-discovery .choice .ok").on("click", function() {
		var tab = $(this).closest("table");
		tab.find(".outcome .amend").css("visibility", "visible").fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);;
	});
	$(".reaction-discovery .choice .bad").on("click", function() {
		var tab = $(this).closest("table");
		tab.find(".outcome .fail").css("visibility", "visible").fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);;
	});

});