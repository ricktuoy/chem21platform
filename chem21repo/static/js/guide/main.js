define(["guide/scores", "guide/route", "jquery", "jquery.cookie", "jquery-ui/droppable", "jquery-ui/draggable"], function(Scores, Route, $) {
    $(function() {
        $.fn.reduce = [].reduce;

        $(".guide .question input.choice").each(function() {
            var $new_div = $("<div />").addClass("choice").insertBefore($(this));
            var $choice = $(this).add($(this).next("label"));
            $new_div.append($choice);
        });

        $(".guide .question").each(function() {
            $(this).addClass($(this).data("type"));
        });



        $(".guide").on("click", "div.choice", function(e) {
            e.stopImmediatePropagation();
            e.preventDefault();
            var $input = $(this).find("input.choice");
            switch($input.attr("type")) {
                case "radio":
                    var prev = $input.prop("checked");
                    $input.prop("checked", true);
                    if(prev == false) {
                        $input.trigger("change");
                    }
                    break;
                case "checkbox":
                    if($input.prop("checked")) {
                        $input.prop("checked", false);
                    } else {
                        $input.prop("checked", true);
                    }
                    $input.trigger("change");
                    break;
            }
        });

        $(".guide").on("click", "input.choice", function(e) {
            e.stopPropagation();
        });

        $(".guide .question").not(":first").hide();

        $(".guide").addClass("unmarked");

        $(".guide").on("click", ".question .controls a", function() {
            var $question = $(this).closest(".question");
            var route = get_route();
            if( $(this).hasClass("prev") ) {
                var go_back = true;
            } else {
                var go_back = false;
            }
            $question.trigger("mark_and_move", [go_back])
        });

        $(".guide").on("click", ".submit", function() {

            $(this).closest(".guide").trigger("mark");
        });

        function get_scores() {
            $quiz = $(".guide");
            var s = $quiz.data("SEH_scores");
            if (!s) {
                return new Scores();
            } else {
                return s;
            }
        }

        function store_scores(scores) {
            $quiz = $(".guide");
            $quiz.data("SEH_scores", scores);
        }

        $(".guide").on("click", ".reset", function(e) {
            e.preventDefault();
            scores = get_scores();
            $(".guide").find("form").trigger("reset");
            scores.reset();
            store_scores(scores);
            route = get_route();
            route.reset();
            var $next_q = route.get_question();
            $(".guide .question").hide();
            $next_q.show();
            store_route(route);
            var $scores = $quiz.find("#she_scores");
            $scores.slideUp();
        });



        function get_route() {
            $quiz = $(".guide");
            var r = $quiz.data("SEH_route");
            if (!r) {
                return new Route($quiz);
            } else {
                return r;
            }
        }

        function store_route(route) {
            $quiz = $(".guide");
            $quiz.data("SEH_route", route);
        }

        function mark_question($q, val) {
            var scores = get_scores();
            var store_val_fn = scores[$q.data("id")];
            store_val_fn(val);
            return scores;
        }

        $(".guide").on("mark_and_move", ".question", function(e, go_back) {
            // save scores
            e.stopImmediatePropagation();
            var $error = $(this).nextAll(".error").eq(0);
            $error.empty();
            var $q = $(this);
            var $field = $q.find("input");

            if($field.length > 1) {
                //choices!
                var val = $field.filter(":checked").val();
            } else if($field.length == 1) {
                var val = $field.val();
            } else {
                $field = $q.find("select");
                var val = $field.val();
            }

            if((val == "" || val == false) && !go_back) {
                // show error 
                var error_msg = $("<p>Please answer this before proceeding.</p>");
                $error.eq(0).append(error_msg);
                return false;
            }
            
            var dk = false; 
            if(val == "y") {
                val = true;
            }
            if(val =="n") {
                val = false;
            }
            if(val =="dk") {
                val = false;
                dk = true;
            }

            if(!go_back) {
                var scores = mark_question($q, val);
            } else {
                var scores = get_scores();
            }

            var route = get_route();
            if(go_back) {
                var skipped_ids = route.prev(scores);
            } else {
                var skipped_ids = route.next(scores);
            }

            // wipe skipped values.
            if(skipped_ids.length > 0) {
                for (var i = 0; i < skipped_ids.length; i++) {
                    scores.update( skipped_ids[i], [0, 0, 0]);
                }
            }

            store_scores(scores);
            var $next_q = route.get_question();
            $(".guide .question").hide();
            $next_q.show();
            store_route(route);
            return true;
        });

        $(".guide").on("mark", function() {
            var $quiz = $(this);
            var scores = get_scores();
            var $reach = $("#question_reach");
            var $field = $reach.find("input");
            var val = $field.filter(":checked").val();
            if(val=="y") {
                val = true;
            } else {
                val = false;
            }
            mark_question($reach, val);          
            var $questions = $quiz.find(".question");
            var s = scores.get_S();
            var s_class = scores.get_S_band();
            var h = scores.get_H();
            var h_class = scores.get_H_band();
            var e = scores.get_E();
            var e_class = scores.get_E_band();

            var $score_s = $("<div id=\"score_s\" />");
            var $score_h = $("<div id=\"score_h\" />");
            var $score_e = $("<div id=\"score_e\" />");
          
            var $p = $("<p />").html(s);
            var $he = $("<h3 />").html("Safety");
            $score_s.append($he);
            $score_s.append($p);
            $score_s.addClass(s_class);
            var $p = $("<p />").html(h);
            var $he = $("<h3 />").html("Health");
            $score_h.append($he);
            $score_h.append($p);
            $score_h.addClass(h_class);
            var $p = $("<p />").html(e);
            var $he = $("<h3 />").html("Environment");
            $score_e.append($he);
            $score_e.append($p);
            $score_e.addClass(e_class);

            var $ranking = $("<div id=\"default_ranking\" />");
            var $p = $("<p />").html(scores.get_default_ranking());
            var $he = $("<h3 />").html("Default ranking");
            $ranking.append($he);
            $ranking.append($p);
            $ranking.addClass(scores.get_default_ranking_band());
            
            var $scores = $quiz.find("#she_scores");
            var $reset = $("<a href=\"#\" class=\"reset\">Rank another solvent</a>");
            $scores.empty();

            $scores.append($score_s);
            $scores.append($score_h);
            $scores.append($score_e);
            $scores.append($ranking);

            $scores.append($reset);
           

            if($scores.filter(":visible").length == 0) {  
                $scores.slideDown();
            } 
            
        });
    });
});