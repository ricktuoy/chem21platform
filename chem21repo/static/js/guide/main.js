define(["guide/scores", "guide/route", "jquery", "jquery.cookie", "jquery-ui/droppable", "jquery-ui/draggable"], function(Scores, Route, $) {
    $(function() {
        $.fn.reduce = [].reduce;

        $(".guide .question").each(function() {
            $(this).addClass($(this).data("type"));
        });

        $(".guide .question").not(":first").hide();

        $(".guide").addClass("unmarked");

        if($(".guide").length) {
            $("#quiz_progress nav, #end-nav").hide();
        }
        /*
        $(".guide").on("change", ".question input, .question select", function() {
            var route = get_route();
            var $quiz = $(".guide");
            var $question = $(this).closest(".question");
            console.debug($question);
            console.debug("change");
            if(!$question.hasClass("single")) {
                return true;
            }
            if(route.at_final()) {
                $quiz.trigger("mark");
            } else {
                $question.trigger("mark_and_move", [false])
            }
            return true;
        });
        */

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

        $(".guide").on("mark_and_move", ".question", function(e, go_back) {
            // save scores
            e.stopImmediatePropagation();
            var scores = get_scores();
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
            console.debug(val);
            if(val == "" || val == false) {
                return false;
            }

            if(val == "y") {
                val = true;
            }

            if(val =="n") {
                val = false;
            }
            var store_val_fn = scores[$q.data("id")];
            store_val_fn(val);

            var route = get_route();

            if(go_back) {
                route.prev(scores);
            } else {
                route.next(scores);
            }

            var $next_q = route.get_question();
            $(".guide .question").hide();
            $next_q.show();
            store_route(route);
            store_scores(scores);
            return true;
        });

        $(".guide").on("mark", function() {
            var $quiz = $(this);
            var scores = get_scores();          
            var $questions = $quiz.find(".question");
            var s = scores.get_S();
            var s_class = scores.get_S_band();
            var h = scores.get_H();
            var h_class = scores.get_H_band();
            var e = scores.get_E();
            var e_class = scores.get_E_band();
            console.debug([s, s_class, e, e_class, h, h_class, scores.get_default_ranking(), scores.get_default_ranking_band()]);

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
            var $he = $("<h3 />").html("Ranking");
            $ranking.append($he);
            $ranking.append($p);
            $ranking.addClass(scores.get_default_ranking_band());
            
            var $scores = $quiz.find("#she_scores");
            $scores.empty();

            $scores.append($score_s);
            $scores.append($score_h);
            $scores.append($score_e);
            $scores.append($ranking);
            
            if($scores.filter(":visible").length == 0) {  
                $scores.slideDown();
            } 
            
        });
    });
});