define(["jquery","../page-menu/selectable-blocks"], function($, Blocks) {

$(function() {

	blocks = new Blocks($("#content-body"));
	blocks.figures.selected_css_class = "edit_selected";
	blocks.figures.selectable_css_class = "edit_selectable";

	$(".admin_menu").on({
		mouseenter: function() {
			$(this).find("ul").show();
		},
		mouseleave: function() {
			$(this).find("ul").hide();
		}
	}, ".category:not(.disabled)");


	$(".admin_menu").on({
		click: function(evt) {

			var link = $(this).find("a");
			var href = link.attr("href");
			var signature = link.data("signature");
			var instruction = link.data("instruction");
			switch(link.data("commandName")) {
				case "addFigure":
					blocks.init_select(signature, href);	
					break;
				case "editFigure":
				case "removeFigure":
					blocks.figures.init_select(signature, href);
					break;
				default:
					if(href) {
						window.location = href;
					}
					return;
			}
			
			$(".admin_menu .category").addClass("disabled");
			$(".admin_menu .category ul").hide();
			evt.preventDefault();
			if(instruction) {
				var $instruction = $("<p id=\"admin_menu_action_instruction\">" + instruction + "</p>");
				$(".admin_menu").after($instruction);
			}
			blocks.$container.on("endSelectWidget", function(evt) {
				$(".admin_menu .category").removeClass("disabled");
				if(instruction) {
					$instruction.remove();
				}
			}); 
		}	
	}, ".command");
});

});