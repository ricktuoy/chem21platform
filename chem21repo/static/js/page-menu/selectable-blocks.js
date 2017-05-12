define(["jquery","selector_widget_mixin"], function($,SelectorWidgetMixin) {
	var S_CONTAINER_PREPEND_ID = "blocks_zeroth";
	var S_CONTENT_BLOCK_FIGURE = "aside,.inline,table";

	Function.prototype.apply_mixin = function(parent) {
		for (var i = 1; i < arguments.length; i+=1) {
			var name = arguments[i];
			this.prototype[name] = parent.prototype[name];
		}
		return this;
	};

	var FinderMixin = function() {}
	FinderMixin.prototype.find = function() {
		return this.$base.filter(this.selector);	
	};

	var NonFigures = function(blocks) {
		this.blocks = blocks;
		this.main = blocks;
		this.$base = blocks.find();
		this.$container = this.blocks.$container;
		this.selector =  ":not(" + S_CONTENT_BLOCK_FIGURE + ")";
	};

	NonFigures.apply_mixin(FinderMixin, 'find');
	NonFigures.apply_mixin(SelectorWidgetMixin, 'build_uri');
	NonFigures.prototype.get_select_click_callback = function() {
		var $elements = this.find();
		var that = this;
		return function(evt) {
			var paragraph = $elements.index(this) + 1;
			var uri  = that.build_uri({para: paragraph, pos: "below", fig: 1});
			window.location = uri;
		};	
	};

	var Figures = function(blocks) {
		this.blocks = blocks;
		this.main = blocks;
		this.$base = blocks.find();
		this.selector = S_CONTENT_BLOCK_FIGURE;
		this.$container = this.blocks.$container;
		this.selectable_css_class = "selectable";
		this.selected_css_class = "selected";
	};

	Figures.apply_mixin(FinderMixin, 'find');
	Figures.apply_mixin(SelectorWidgetMixin, 
		'init_select', 
		'get_end_select_click_callback', 
		'build_uri');
	Figures.prototype.get_select_click_callback = function() {
		var non_selector = this.blocks.non_figures.selector;
		var selector = this.selector;
		var that = this;
		return function(evt) {
			var $this = $(this);
			var $next_non_figs = $this.nextAll(non_selector);
			var $prev_non_figs = $this.prevAll(non_selector);
			if($next_non_figs.length == 0) {
				console.debug("No paragraph found for this figure!");
				return;
			} 
			var next_non_fig = $next_non_figs[0];
			var paragraph = that.blocks.non_figures.find().index(next_non_fig);
			if($prev_non_figs.length > 0) {
				var prev_non_fig = $prev_non_figs[0];
				var $cluster = $(prev_non_fig).nextUntil(non_selector).filter(selector);
				var order = $cluster.index(this) + 1;
			} else {
				var $cluster = $(next_non_fig).prevAll().filter(selector);
				var order = $cluster.length - $cluster.index(this);
			}
			var uri  = that.build_uri({para: paragraph, pos: "below", fig: order});
				window.location = uri;
		};
	};
	
	var Blocks = function($base) {
		this.$base = $base;
		this.$container = this.$base;
		this.selector = ">*";
		this.selectable_css_class = "selectable";
		this.selected_css_class = "selected";
		this.figures = new Figures(this);
		this.non_figures = new NonFigures(this);
		this.main = this;
		this.blocks = this;
		this.uri_type = "segments";
	};

	Blocks.prototype.find = function() {
		return this.$base.find(this.selector);
	};

	Blocks.apply_mixin(SelectorWidgetMixin, 'build_uri')
	Blocks.prototype.get_select_click_callback = function() {
		var figure_callback = this.figures.get_select_click_callback.call(this.figures);
		var non_figure_callback = this.non_figures.get_select_click_callback.call(this.non_figures);
		var that = this;
		return function(evt) {
			var $this = $(this);

			var $isNonFigure = $this.filter(that.non_figures.selector);
			if($isNonFigure.length > 0) {
				return non_figure_callback.call(this,evt);
			} else {
				return figure_callback.call(this,evt);
			}
		};
	};

	Blocks.prototype.init_select = function(signature, uri) {
		SelectorWidgetMixin.prototype.init_select.call(this, signature, uri);
		var that = this;
		this.$prepended = $("<div id=\"" + S_CONTAINER_PREPEND_ID + "\" class=\"" + this.selectable_css_class + "\">&nbsp</div>");
		this.$base.before(this.$prepended);
		this.$prepended.on({
			"mouseenter.selectorWidget": function(evt) {
				$(this).addClass(that.selected_css_class);				
			},
			"mouseleave.selectorWidget": function(evt) {
				$(this).removeClass(that.selected_css_class);
			},
			"click.selectorWidget": function(evt) {
				var uri = that.build_uri({para: 0, pos: "below", fig: 1});
				window.location = uri;
			}
		});
	};
	Blocks.prototype.get_end_select_click_callback = function() {
		var that = this;
		return function(evt) {
			SelectorWidgetMixin.prototype.get_end_select_click_callback.call(that)(evt);
			that.$prepended.remove();
		}
	}

	return Blocks;

});
