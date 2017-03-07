define(["jquery", "jquery.cookie", "jquery-ui/droppable", "jquery-ui/draggable"], function($) {
    $(function() {
        $.fn.reduce = [].reduce;
        $.fn._quiz_choice_class = function() {
            if(!this.length) {
                return false;
            }
            return "div.choice";
        };

        $.fn.quiz_find_choices = function() {
            var cls = this._quiz_choice_class();
            if(!cls)  {
                return $();
            }
            return this.find(cls);
        };

        $.fn.quiz_closest_choice = function() {
            var cls = this._quiz_choice_class();
            if(!cls) {
                return $();
            }
            return this.closest(cls);
        };

        $.fn.quiz_get_choice = function(id) {
            var cls = this._quiz_choice_class();
            if(!cls) {
                return $();
            }
            return this.find(cls).has("input[data-id=\""+id+"\"]");
        };

        $(".quiz_questions .question").each(function() {
            $(this).addClass($(this).data("type"));
        });

        $(".quiz_questions .question input.choice").each(function() {
            var $new_div = $("<div />").addClass("choice").insertBefore($(this));
            var $choice = $(this).add($(this).next("label"));
            $new_div.append($choice);
        });

        $(".quiz_questions").on("click", "div.choice", function(e) {
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


        $(".quiz_questions").on("click", "input.choice", function(e) {
            e.stopPropagation();
        });

        $(".quiz_questions .question").not(":first").hide();

        $(".quiz_questions .reveal-answer").hide();

        $(".quiz_questions .submit").hide();

        $(".quiz_questions").addClass("unmarked");

        if($(".quiz_questions").length) {
            $("#quiz_progress nav, #end-nav").hide();
        }

        $(".quiz_questions").on("change", ".question input", function() {
            var $question = $(this).closest(".question");
            if($question.hasClass("marked")) {

            } else {
                var num_chosen = $question.quiz_find_choices().has("input:checked").length;
                var $skip_c = $question.find(".controls a.skip");
                var $next_c = $question.find(".controls a.next");
                if(num_chosen > 0 && $skip_c.length) {
                    $skip_c.removeClass("skip");
                    $skip_c.addClass("next");
                    $skip_c.html("Submit &raquo;");
                }
                if(num_chosen == 0 && $next_c.length) {
                    $next_c.removeClass("next");
                    $next_c.addClass("skip");
                    $next_c.html("Skip question &raquo;");
                }
            }
        });

        $(".quiz_questions").on("responseClear", ".question",  function(e) {
            $(this).data("response", {});
            $(this).trigger("refreshResponses");
        });

        $(".quiz_questions").on("moveForward", function(e, fromEl) {
            if($(this).hasClass("marked")) {
                return true;
            }
            var current = $(this).find(":visible");
            current.hide().next().show();
        });

        $(".quiz_questions").on("move", function(e, dest) {
            if($(this).hasClass("marked")) {
                return true;
            }

            $(this).find(".question").hide();
            dest.show();
        });
        
        $(".quiz_questions").on("click", ".question .controls a.skip", function() {
            var $skip = $(this);
            $(this).closest(".question").data("skipped", true);
        });

        $(".quiz_questions").on("click", ".question .controls a", function() {
            var $question = $(this).closest(".question");
            if($question.hasClass("marked")) {
                var id = $(this).attr("href");
                var target = $(".question"+id);
                if( target.length>0 ) {
                    $(this).closest(".quiz_questions").trigger("move", [target]);
                }
            } else {
                $question.trigger("mark");
            }
        });

        $(".quiz_questions").on("click", ".submit", function() {
            $(this).closest(".quiz_questions").trigger("mark");
        });

        $(".quiz_questions").on("mark", ".question", function(e) {
            if($(this).hasClass("marked")) {
                return false;
            }
            var $quiz = $(this).closest(".quiz_questions");
            var $q = $(this);

            var processor = function(question) {
                if($q.data("skipped")) {
                    $q.quiz_find_choices().removeClass("unchosen").removeClass("chosen").addClass("skipped");
                }
                var answer_texts = [];
                var $title = $("h3", $q).first();
                
                $.each(question.correct, function(i, rId) {
                    var $c = $q.quiz_get_choice(rId);
                    $c.addClass("correct");
                });

                var $choices = $q.quiz_find_choices();
                $choices.find("input").prop("disabled", true)
                var $chosen = $choices.has("input:checked");
                $chosen.addClass("chosen");
                var $correct = $choices.filter(".correct").detach();
                var $incorrect = $choices.not(".correct").detach();
                
                $chosen.not($correct).addClass("incorrect");

                var $controls = $q.find(".controls");
                $controls.before($("<div class=\"marked_choices\"></div>"));
                var $marked_choices = $q.find(".marked_choices");

                if($correct.length) {
                    var $correct_choice_container = $("<fieldset class=\"all_correct\" data-role=\"controlgroup\"><legend>Correct responses</legend></fieldset>")
                    $correct_choice_container.appendTo($marked_choices).append($correct);
                }

                if($incorrect.length) {
                    var $incorrect_choice_container = $("<fieldset class=\"all_incorrect\" data-role=\"controlgroup\"><legend>Incorrect responses</legend></fieldset>");
                    $incorrect_choice_container.appendTo($marked_choices).append($incorrect);
                }

                //$marked_choices.enhanceWithin();

                var $question_score = $q.find(".final_score");
                
                var percentage_score = 0;

                switch($q.data("type")) {
                    case 'single':
                        // right or wrong
                        var num_good = $chosen.filter(".correct").length;
                        if(num_good) {
                            percentage_score = 100;
                        }
                        var responses = $chosen.first().find("input").val(); 
                        break;

                    case 'multi':
                        // actual percentage
                        var num_choices = $choices.length;
                        var num_good = $chosen.filter(".correct").length + $incorrect.not($chosen).length;
                        percentage_score = Math.round((num_good  / num_choices) * 100 );
                        var responses = [];
                        $chosen.each( function() {
                            responses.push($(this).find("input").val());
                        });
                        break;
                }
                
                var skipped_msg = "";
                
                var $next = $controls.find(".skip, .next");
                    $next.removeClass("skip");
                    $next.addClass("next");
                    $next.html("Continue quiz &raquo;");
                

                if($q.data("skipped")) {
                    skipped_msg = " (skipped).";
                }
                
                $question_score.append("<span class=\"label\">Your question score: </span><span class=\"score\">" + 
                    percentage_score + "%" + skipped_msg + "</span>");

                $q.data("possible_score", 100);
                $q.data("actual_score", percentage_score);

                $q.find(".help").hide();
                
                var $next = $q.next();
                $q.find("a.submit").show();
                if($next.length == 0) {
                    var $cont = $q.find(".controls a.next");
                    $cont.hide();
                }

                if(question.discussion) {
                    var $discussion = $("<div class=\"discussion\" />");
                    $discussion.html(question.discussion);
                    $question_score.after($discussion);
                } else {
                }

                $q.addClass("marked");
                $q.trigger("marking-done", [responses]);
            }
            
            var qdef = $q.data("definition");
            if(typeof(qdef) == "undefined") {
                var url = $quiz.data("answersJsonUrl");
                var out = $.getJSON(url, function(data) {
                    $.each(data.data, function(i, question) {
                        var $qq = $quiz.find(".question#question_"+question.id);
                        $qq.data("definition", question);
                    });
                    processor($q.data("definition"));
                });
            } else {
                processor(qdef);
                var out = true;
            }

            e.stopPropagation();
            return out;
        });

        $(".quiz_questions").on("mark", function() {
            var $quiz = $(this);
            
            var $questions = $quiz.find(".question");
            var total_possible = $questions.reduce(function(prev, curr, i, arr) {
                var r = prev + $(curr).data("possible_score");
                return r;
            }, 0);
            
            var total_good = $questions.reduce(function(prev, curr, i, arr) {
                var r = prev + $(curr).data("actual_score");
                return r;
            }, 0);
            $quiz.prepend("<p class=\"quiz_total\"><span class=\"label\">Your quiz score: </span>" + (Math.round(( total_good / total_possible) * 100)) +"%</p>");
            $quiz.find(".question .controls").hide();
            $quiz.find(".question .submit").hide();
            $quiz.find(".question").show();
            $("#end-nav, #quiz_progress nav").show();


        });
    });
});