define(["jquery", "jquery.cookie", "jquery-ui/droppable", "jquery-ui/draggable"], function($) {
    $(function() {

        $(".quiz_questions .question").not(":first").hide();

        $(".quiz_questions .reveal-answer").hide();

        $(".quiz_questions").addClass("unmarked");

        $(".question").on("responseAdd", function(e, source) {
            if($(this).closest(".quiz_questions").hasClass("marked")) {
                return true;
            }
            var d = $(this).data("response");
            var id = source.data("id");
            if(typeof(d)=="undefined") {
                d = {};
            }
            if(!(id in d)) {
                d[id] = true;
                $(this).data("response", d);
            }
            $(this).trigger("refreshResponses");
        });

        $(".question").on("refreshResponses", function() {
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

        $(".question").on("responseClear", function(e) {
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

        $(".question[data-type=\"single\"] .choice").on("click", function() {
            $(this).closest(".question").trigger("responseClear");
            $(this).closest(".question").trigger("responseAdd", [$(this)] );
            var next = $(this).closest(".question").next();
            if(next.length > 0) {
                $(this).closest(".quiz_questions").trigger("move", [next]);
            } else {
                $(this).closest(".quiz_questions").trigger("mark");
            }
        });

        $(".question[data-type=\"multi\"] .choice").on("click", function() {
            $(this).closest(".question").trigger("responseAdd", [$(this)] );
        });

        $(".question .controls a").on("click", function() {
            var id = $(this).attr("href");
            var target = $(".question"+id);
            if( target.length>0 ) {
                $(this).closest(".quiz_questions").trigger("move", [target]);
            }
        });

        $(".quiz_questions .submit").on("click", function() {
            $(this).closest(".quiz_questions").trigger("mark");
        });

        $(".quiz_questions").on("mark", function() {
            if($(this).closest(".quiz_questions").hasClass("marked")) {
                return true;
            }
            var url = $(this).data("answersJsonUrl");
            var quiz = $(this);
            $.getJSON(url, function(data) {
                quiz.addClass("marked");
                quiz.removeClass("unmarked");
                var total_possible = 0;
                var total_good = 0;
                $.each(data.data, function(i, question) {
                    var answer_texts = [];
                    var $q = quiz.find(".question#question_"+question.id);
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

                    var $scores = $("<div class=\"scores\" />"); 
                    $scores.append("<p><span class=\"label\">Correct answers:</span> "+answer_texts.join("; ")+".</p>");
                    $scores.append("<p><span class=\"label\">Your answers:</span> "+chosen_texts.join("; ")+".</p>");
                    var num_choices = $q.find(".choice").length;
                    var num_good = $q.find(".choice.incorrect.unchosen, .choice.correct.chosen").length;
                    var percentage_score = Math.round((num_good  / num_choices) * 100 );
                    $scores.append("<p><span class=\"label\">Question score:</span> " + percentage_score + "%</p>");
                    total_possible += 100;
                    total_good += percentage_score;
                    $q.append($scores);
                    if("discussion" in question) {
                        $q.append($("<div class=\"discussion\" />").html(question.discussion));
                    }
                });
                quiz.prepend("<p class=\"totals\"><span class=\"label\">Your total score for this quiz: </span>" + (Math.round(( total_good / total_possible) * 100)) +"%</p>");

                $(".question .controls").hide();
                $(".question .submit").hide();
                $(".question").show();
            });
        });
    });
});