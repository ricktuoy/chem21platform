define(["jquery", "jquery.colorbox", "jquery.mjs.nestedSortable"], function($) {
    //the jquery.alpha.js and jquery.beta.js plugins have been loaded.
    var isDropAllowed = function (placeholder, placeholderParent, currentItem) { return true; }
    $(function() {
        $(".file_type_video").colorbox({onComplete : function() {$(this).colorbox.resize()} }  );
		var ns = $('ol.sortable').nestedSortable({
			forcePlaceholderSize: true,
			handle: 'div',
			items: 'li',
			toleranceElement: '> div',
			opacity: .6,
			revert: 250,
			tabSize: 25,
			maxLevels: 5,
			isTree: true,
			expandOnHover: 100,
			startCollapsed: false,
			disableParentChange:true,
			isAllowed: isDropAllowed
		});
    });
});