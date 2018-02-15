/**
 * Lineselect jQuery plugin
 *
 * Make containers of lines show selection line-by-line.
 * Good for highlighting lines of code.
 * 
 * Based on https://github.com/nedbat/prznames/blob/master/lineselect.js
 * by Ned Batchelder
 * Copyright 2011
 * @license MIT License
 */
(function ($) {
    // Internal constants
    var container_class = "lineselect_selectable";
    var sub_class = "span.line";
    
    // Global options
    var options = {
        focus: ".focus",
        active_sel: "section.present"
    };

    var select_line = function (container, line, single) {
        if (single) {
            deselect_all(container);
        }
        line.addClass("selected");
        line.trigger("lineselected");
    };

    var select_line_by_number = function (container, lineno, single) {
		//console.log('select_line_by_number ' + lineno + ' ' + single);
        var the_line = $(container.find(sub_class)[lineno-1]);
        select_line(container, the_line, single);
    };

    var deselect_all = function (container) {
        container.find(sub_class).removeClass("selected");
    };

	var dom = {};

	function lineSelectionActive() {
		return dom.wrapper.classList.contains('selecting-lines');
	};

	function enableLineSelection() {
		//console.log('lineselect: enabling');
		dom.wrapper.classList.add('selecting-lines');
	};

	function disableLineSelection() {
		//console.log('lineselect: disabling');
		dom.wrapper.classList.remove('selecting-lines');
	};

	function toggleLineSelection( override ) {
		if( typeof override === 'boolean' ) {
			override ? enableLineSelection() : disableLineSelection();
		}
		else {
			lineSelectionActive() ? disableLineSelection() : enableLineSelection();
		}
	};

    var keydown_fn = function (e) {
		//console.log('lineselect.keydown_fn' + e.keyCode);
        // Find the one container to manipulate.
        var container = $(options.active_sel + " ." + container_class + options.focus_class + ":visible");
        if (container.length === 0) {
            container = $(options.active_sel + " ." + container_class + ":visible");
        }
        if (container.length === 0) {
            //console.log("looking for", options.active_sel + "." + container_class);
            container = $(options.active_sel + "." + container_class);
        }
        if (container.length !== 1) {
            //console.log("Done, not 1", container_class, container.length);
            return;
        }

        var the_selected = container.find(sub_class + ".selected"), 
            selected = 0;
        if (the_selected.length) {
            var all_lines = container.find(sub_class);
            selected = all_lines.index(the_selected) + 1;
        }

        switch (e.keyCode) {

	    case 190:  // toggle using blank screen button on logitech remote
			//console.log('lineselect:toggle');
			toggleLineSelection();
			if (lineSelectionActive()) {
				selected = 1;
			} else {
				deselect_all(container);
				return;
			}
			break;

        case 71:    // G: top
            selected = 1;
            break;

		case 78: case 34:  // logitech remote
        case 74:    // J: down
			if (lineSelectionActive()) {
				//console.log('lineselect: down');
				selected += 1;
			} else {
				//console.log('lineselect: inactive');
			}
            break;

		case 80: case 33:  // logitech remote
        case 75:    // K: up
			if (lineSelectionActive()) {
				//console.log('lineselect: up');
				selected -= 1;
			} else {
				//console.log('lineselect: inactive');
			}
            break;

        // case 190:   // .: deselect
        case 88:    // X: deselect
            deselect_all(container);
            return;

        default:
            //console.log('down: ' + e.keyCode);
            return;
        }

		//console.log('lineselect: ' + container.html());
		//console.log('lineselect: ' + sub_class + ' ' + selected + ' ' + container.find(sub_class).length);
        if (selected < 1 || selected > container.find(sub_class).length) {
            return;
        }
        var single = !e.shiftKey;
        select_line_by_number(container, selected, single);
    };

    var make_line_selectable = function (elements, opts) {
        // Register a document keydown function once.
        if (keydown_fn) {
            $(document).keydown(keydown_fn);
            keydown_fn = null;
        }
        // Apply the options, some are global.
        $.extend(options, opts);

		dom.wrapper = document.querySelector( '.reveal' );
		dom.slides = document.querySelector( '.reveal .slides' );

		//console.log('making lines selectable');

        // In every container, find all the "lines", mark them, and give them
        // click handlers.
        return elements.each(function () {
            var container = $(this);
			//console.log('BEFORE: ', container.html());
            container.addClass(container_class);
            container.find(opts.lines)
                .addClass(sub_class)
                .on('click',
                    function (e) { 
                        select_line(container, $(this), !e.ctrlKey);
                    }
                );
			//console.log('AFTER: ', container.html());
        });
    };

    $.fn.lineselect = function (arg) {
        if (typeof arg === "object" || typeof arg === "undefined") {
            // Make elements line-selectable
            make_line_selectable(this, arg);
            return this;
        }
        else if (typeof arg === "string") {
            arg = arg.split(",");
        }
        else {
            arg = [arg];
        }

        this.each(function () {
            var that = $(this);
            deselect_all($(this));
            $.each(arg, function (i, a) {
                a = +a;
                select_line_by_number(that, a, false);
            });
        });

        return this;
    };

}(jQuery));
