define(["jquery", "jquery.cookie", "jquery-ui/droppable", "jquery-ui/draggable"], function($) {
    $(function() {
        $.fn.reduce = [].reduce;

        $(".quiz_questions .question").not(":first").hide();

        $(".quiz_questions .reveal-answer").hide();

        $(".quiz_questions").addClass("unmarked");

        $(".quiz_questions").on("responseAdd", ".question", function(e, source) {
            if($(this).closest(".quiz_questions").hasClass("marked")) {
                return true;
            }

            var d = $(this).data("response");
            var id = source.data("id");
            var skip = $(this).find(".controls a.skip");
            var $next = $(this).next(); 
            if(skip.length > 0) {
              
                    skip.removeClass("skip");
                    skip.addClass("next");
                    skip.html("Continue");
                
            }
            if(typeof(d)=="undefined") {
                d = {};
            }
            if(!(id in d)) {
                d[id] = true;
                $(this).data("response", d);
            }
            $(this).trigger("refreshResponses");
        });

        $(".quiz_questions").on("refreshResponses", ".question", function() {
            var d = $(this).data("response");
            var choices = $(this).find(".choice");
            choices.addClass("unchosen");
            choices.removeClass("chosen");
            choices.each(function() {
                if($(this).data("id") in d) {
                    $(this).addClass("chosen");
                    $(this).removeClass("unchosen");
                }
            });
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

        $(".quiz_questions").on("click", ".question.marked .choice", function(e) {
            console.debug("Choice of previously marked question");
            e.stopImmediatePropagation();
        });

        $(".quiz_questions").on("click", ".question[data-type=\"single\"] .choice", function() {
            $(this).closest(".question").trigger("responseClear"); 
        });

        $(".quiz_questions").on("click", ".question .choice", function() {
            $(this).closest(".question").trigger("responseAdd", [$(this)] );
        });

        $(".quiz_questions").on("click", ".question[data-type=\"single\"] .choice", function() {
            $(this).closest(".question").trigger("mark"); 
        });

        $(".quiz_questions").on("click", ".question .controls a.skip", function() {
            var $skip = $(this);
            $skip.removeClass("skip");
            $skip.addClass("next");
            $skip.html("Continue");
            $(this).closest(".question").data("skipped", true);
        });

        $(".quiz_questions").on("click", ".question .controls a", function() {
            console.debug("Generic control click");
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
                return;
            }
            var $quiz = $(this).closest(".quiz_questions");
            var $q = $(this);
            var processor = function(question) {
                if($q.data("skipped")) {
                    $q.find("choice").removeClass("unchosen").removeClass("chosen").addClass("skipped");
                }
                var answer_texts = [];
                $q.find(".choice").addClass("incorrect");
                $.each(question.correct, function(i, rId) {
                    var $c = $q.find(".choice[data-id=\""+rId+"\"]");
                    $c.removeClass("incorrect");
                    $c.addClass("correct");
                    answer_texts.push($c.html());
                });
                var chosen_texts = $q.find(".choice.chosen").map(function() {
                    return $(this).html();
                }).get();
                var $scores = $("<div class=\"answers\" />"); 
                var $question_score = $q.find(".final_score");
                $scores.append("<p><span class=\"label\">Correct answers:</span> "+answer_texts.join("; ")+".</p>");
                if(!$q.data("skipped")) {
                    $scores.append("<p><span class=\"label\">Your answers:</span> "+chosen_texts.join("; ")+".</p>");
                }
                var num_choices = $q.find(".choice").length;
                var num_good = $q.find(".choice.incorrect.unchosen, .choice.correct.chosen").length;
                var percentage_score = Math.round((num_good  / num_choices) * 100 );
                var skipped_msg = "";
                var $controls = $q.find(".controls");

                if($q.data("skipped")) {
                    skipped_msg = " (skipped).";
                }
                $question_score.append("<span class=\"label\">Your question score: </span><span class=\"score\">" + 
                    percentage_score + "%" + skipped_msg + "</span>");

                $q.data("possible_score", 100);
                $q.data("actual_score", percentage_score);
                $controls.before($scores);
                console.debug("Question");
                console.debug(question);

                $q.find(".help").hide();
                $q.addClass("marked");
                $next = $q.next();
                if($next.length == 0) {
                    var $cont = $q.find(".controls a.next");
                    $cont.hide();
                }
                if(question.discussion) {
                    var $discussion = $("<div class=\"discussion\" />");
                    $discussion.html(question.discussion);
                    $question_score.after($discussion);
                    $controls.detach().insertAfter($discussion);
                } else {
                    $controls.detach().insertAfter($question_score);
                }

                
            }
            
            var qdef = $q.data("definition");
            if(typeof(qdef) == "undefined") {
                var url = $quiz.data("answersJsonUrl");
                $.getJSON(url, function(data) {
                    $.each(data.data, function(i, question) {
                        var $qq = $quiz.find(".question#question_"+question.id);
                        $qq.data("definition", question);
                    });
                    processor($q.data("definition"));
                });
            } else {
                processor(qdef);
            }

            e.stopImmediatePropagation();
        });

        $(".quiz_questions").on("mark", function() {
            var $quiz = $(this);
            console.debug("Possible count");
            var $questions = $quiz.find(".question");
            var total_possible = $questions.reduce(function(prev, curr, i, arr) {
                var r = prev + $(curr).data("possible_score");
                console.debug(r);
                return r;
            }, 0);
            console.debug("Good count");
            var total_good = $questions.reduce(function(prev, curr, i, arr) {
                var r = prev + $(curr).data("actual_score");
                console.debug(r);
                return r;
            }, 0);
            $quiz.prepend("<p class=\"quiz_total\"><span class=\"label\">Your quiz score: </span>" + (Math.round(( total_good / total_possible) * 100)) +"%</p>");
            $quiz.find(".question .controls").hide();
            $quiz.find(".question .submit").hide();
            $quiz.find(".question").show();

        });
    });
});