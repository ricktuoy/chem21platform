define([ "jquery", "jquery-ui/tooltip"], function($) {
	$(function() {
		$("#content a.glossary_term").tooltip(          
			{content: function () {
              return $(this).prop('title');
          	}
          });
	});
});