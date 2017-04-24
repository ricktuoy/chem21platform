define(["jquery"], function($) {
	var SelectorWidgetMixin = function() {}
	SelectorWidgetMixin.prototype.init_select = function(signature, uri) {
		this.main.signature = signature;
		this.main.uri = uri;
		var that = this;
		$elements = this.find();
		$elements.addClass(this.selectable_css_class);
		console.debug(this.$container);
		this.$container.on({
			"mouseenter.selectorWidget": function(evt) {
				console.debug(that.selected_css_class);
				$(this).addClass(that.selected_css_class);
			},
			"mouseleave.selectorWidget": function(evt) {
				$(this).removeClass(that.selected_css_class);
			},
			"click.selectorWidget": this.get_select_click_callback()
		}, this.selector);
		this.$end_button = $("<button id=\"end_select\">Cancel</button>");
		this.$container.before(this.$end_button);
		$(this.$end_button).on({
			click: this.get_end_select_click_callback()
		});	
	};

	SelectorWidgetMixin.prototype.get_end_select_click_callback = function() {
		var that = this;
		return function(evt) {
			var $elements = that.find();
			$elements.removeClass(that.selectable_css_class);
			$elements.removeClass(that.selected_css_class);
			that.$container.off(".selectorWidget", that.selector);
			that.$end_button.remove();
			$(that.$container).trigger("endSelectWidget");
		}
	}

	SelectorWidgetMixin.prototype.build_uri = function(props) {
		var out = this.main.uri;
		switch(this.main.uri_type) {
			case 'query_string':
				out += "?"; 
				$.each(this.main.signature.split(","), function() {
					out += this + "=" + props[this] + "&";
				});
				return out.substr(0,out.length-1);
			case 'segments':
				var segs = this.main.uri.split("/");
				var sig_segs = this.main.signature.split(",");
				var add_segs = [];
				$.each(sig_segs, function() {
					do {
						var seg = segs.pop();
					} while(seg === "");
					add_segs.push(props[this]);
				});
				var out_segs = segs.concat(add_segs);
				return out_segs.join("/");
		}
	} 

	return SelectorWidgetMixin;
});