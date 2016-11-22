$(document).ready(function() {	
	$(".reaction-discovery").not("*:first").hide();
	$(".reaction-discovery .outcome td").css("visibility","hidden");
	$(".reaction-discovery .intro").hide();
	$(".reaction-discovery .choice td").show();
	$(".reaction-discovery tbody tr.outcome").hide();

	function show_next_reaction(el) {
		var react = el.closest(".reaction-discovery");
		var tabs = react.find(".flow-chart");
		var fail = false;
		tabs.each(function() {
			var selected = $(this).find(".choice .selected");
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
	$(".reaction-discovery th").click(function() {
		var react = $(this).closest(".reaction-discovery");
		react.find(".intro").slideToggle();
		var tab = $(this).closest(".flow-chart");
		tab.find("tbody").show();
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