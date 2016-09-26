        
define([], function() {
    var Route = function($quiz) {
        this.$questions = $quiz.find(".question");
        this.pos = 0;

        this.reset = function() {
            this.pos = 0;
        }

        this.skip = function(n) {
            var from_pos = this.pos;
            this.pos += n;
            if (this.pos >= this.$questions.length) {
                this.pos = this.$questions.length - 1;
            } else if (this.pos < 0) {
                this.pos = 0;
            }
            for(p = from_pos; p <= this.pos; p++) {

            }
            var skipped_ids = [];
            if( from_pos > this.pos ) {
                var to_pos = from_pos;
                from_pos = this.pos + 1;      
            } else {
                var to_pos = this.pos;
                from_pos++;
            }
            if( n != 1 && n != -1 ) {
                $to_wipe = this.$questions.slice(from_pos, to_pos);
                $to_wipe.each(function() {
                    var $q = $(this);
                    var id = $q.data("id");
                    skipped_ids.push(id);
                });
            }
            return skipped_ids;
        };


        this.can_move_forward = function() {
            if (this.pos >= this.$questions.length - 1 ) {
                return false;
            }
            return true;
        };


        this.at_final = function() {
            return !this.can_move_forward();
        };

        this.can_move_backward = function() {
            if (this.pos > 0) {
                return true;
            }
            return false;
        };

        this.get_question = function() {
            return this.$questions.eq(this.pos);
        }

        this.current_id = function() {
            return this.get_question().data("id");
        }

        this.get_val = function(q_id) {
            if(q_id) {
                var $qn = this.$questions.filter('*[data-id="'+q_id+'"]');
            } else {
                var $qn = this.get_question();
            }
            var $field = $qn.find("input");
            if($field.length > 1) {
                //choices!
                var val = $field.filter(":checked").val();
            } else if($field.length == 1) {
                var val = $field.val();
            } else {
                $field = $qn.find("select");
                var val = $field.val();
            }
            return val;
        }

        this.next = function(scores) {
            var id = this.current_id();
            var is_symbol = /^symbol_.*$/.test(id);
            if(id == "symbol_1" && scores.has_score(id) && scores.H[id]) {
               var skipped = this.skip(5);
            } else if (id == "h340" && scores.has_score(id) && scores.H[id] > 2) {
               var skipped = this.skip(4);
            } else if (id == "h341" && scores.has_score(id) && scores.H[id] > 2) {
                var skipped = this.skip(3);
            } else if (id == "h370" && scores.has_score(id) && scores.H[id] > 2) {
                var skipped = this.skip(2);
            } else if(is_symbol && id != "symbol_4" && scores.has_score(id)) {
               var skipped = this.skip(2);
            } else if(id == "resistivity" && this.get_val("resistivity") != "dk") {
                var skipped = this.skip(2);
            } else {
               var skipped = this.skip(1);
            }
            return skipped;
        };

        this.prev = function(scores) {
            var id = this.current_id();
            var prev_id = "";
            switch(id) {
                case "reach":
                    prev_id = "symbol_5";
                    break;
                case "symbol_4":
                    prev_id = "symbol_3";
                    break;
                case "symbol_3":
                    prev_id = "symbol_2";
                    break;
                case "symbol_2":
                    prev_id = "symbol_1";
                    break;
            }
            var out = false;
            if(id == "ether_explosive_peroxide" && this.get_val("resistivity") != "dk") {
                return this.skip(-2);
            }
            if(prev_id != "" && scores.has_score(prev_id)) {
                if (id=="symbol_2") {
                    return this.skip(-5);
                }
                else {
                    return this.skip(-2);
                }
            }
            if(id=="symbol_2") {
                if(scores.has_score("h334")) {
                    return this.skip(-1);
                } else if (scores.has_score("h370")) {
                    return this.skip(-2);
                } else if (scores.has_score("h341")) {
                    return this.skip(-3);
                } else if (scores.has_score("h340")) {
                    return this.skip(-4);
                } else {
                    console.debug("Error: routing makes no sense. no scores for H statements or symbol 1.")
                }
            }
            return this.skip(-1);
        }
    };
    return Route;
});