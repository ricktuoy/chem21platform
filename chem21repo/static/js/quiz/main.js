define(["jquery", "jquery.cookie", "jquery-ui/droppable", "jquery-ui/draggable"], function($) {
    $(function() {
        $.fn.reduce = [].reduce;

        $(".quiz_questions .question").each(function() {
            $(this).addClass($(this).data("type"));
        });

        $(".quiz_questions .question").not(":first").hide();

        $(".quiz_questions .reveal-answer").hide();

        $(".quiz_questions .submit").hide();

        $(".quiz_questions").addClass("unmarked");

        if($(".quiz_questions").length) {
            $("#quiz_progress nav, #end-nav").hide();
        }

        $(".quiz_questions .choice").each(function() {
            var $q = $(this).closest(".question");
            if($q.hasClass("single")) {
                var itype = "radio";
            } else {
                var itype = "checkbox";
            }

            $(this).prepend($("<input type=\""+itype+"\" name="+$q.data("id") + " value=\""+$(this).data("id")+"\" />"));
        });

        $(".quiz_questions").on("responseAdd", ".question", function(e, source) {
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

        $(".quiz_questions").on("responseRemove", ".question", function(e, source) {
            if($(this).closest(".quiz_questions").hasClass("marked")) {
                return true;
            }
            var d = $(this).data("response");
            var id = source.data("id");
            delete d[id];
            $(this).data("response", d);
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

            console.log($(this).data("id"));
            console.log($("input[name="+$(this).data("id")+"]"));
            console.log(d);
            var keys = []
            for (var key in d) {
                keys.push(key);
            }
            $("input[name="+$(this).data("id")+"]").val(keys);
            
            if($(this).hasClass("marked")) {

            } else {
                var num_chosen = Object.keys(d).length;
                var $skip_c = $(this).find(".controls a.skip");
                var $next_c = $(this).find(".controls a.next");
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

        $(".quiz_questions").on("click", ".question.marked .choice", function(e) {
            e.stopImmediatePropagation();
        });

        $(".quiz_questions").on("click", ".question[data-type=\"single\"] .choice", function() {
            $(this).closest(".question").trigger("responseClear"); 
        });

        $(".quiz_questions").on("click", ".question .choice", function() {
            if($(this).hasClass("chosen")) {
                $(this).closest(".question").trigger("responseRemove", [$(this)] );
            } else {
                $(this).closest(".question").trigger("responseAdd", [$(this)] );
            }
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
                return;
            }
            var $quiz = $(this).closest(".quiz_questions");
            var $q = $(this);
            var processor = function(question) {
                if($q.data("skipped")) {
                    $q.find("choice").removeClass("unchosen").removeClass("chosen").addClass("skipped");
                }
                var answer_texts = [];
                var $title = $("h3", $q).first();
                
                $.each(question.correct, function(i, rId) {
                    var $c = $q.find(".choice[data-id=\""+rId+"\"]");
                    $c.addClass("correct");
                });

                $q.find(".choice input").prop("disabled", true);
                var $chosen = $q.find(".choice.chosen");
                var $correct = $q.find(".choice.correct").detach();
                var $incorrect = $q.find(".choice").detach();
                console.debug($chosen);


                $chosen.not($correct).addClass("incorrect");

                var $controls = $q.find(".controls");


                if($correct.length) {
                    $controls.before($("<p>Correct responses:</p><ul class=\"all_correct\"></ul>"));
                    $correct.appendTo($q.find("ul.all_correct"));
                }

                if($incorrect.length) {
                    $controls.before($("<p>Incorrect responses:</p><ul class=\"all_incorrect\"></ul>"));
                    $incorrect.appendTo($q.find("ul.all_incorrect"));
                }

 
                var $question_score = $q.find(".final_score");
                
                var percentage_score = 0;
                switch($q.data("type")) {
                    case 'single':
                        // right or wrong
                        var num_good = $chosen.filter(".correct").length;
                        if(num_good) {
                            percentage_score = 100;
                        }
                        break;

                    case 'multi':
                        // actual percentage
                        var num_choices = $q.find(".choice").length;
                        console.debug($q.find(".choice"));
                        var num_good = $chosen.filter(".correct").length + $incorrect.not(".chosen").length;
                        console.debug($chosen);
                        console.debug($incorrect.not(".chosen"));
                        percentage_score = Math.round((num_good  / num_choices) * 100 );
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
                    // $controls.detach().insertAfter($discussion);
                } else {
                    // $controls.detach().insertAfter($question_score);
                }

                $q.addClass("marked");
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