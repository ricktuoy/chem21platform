        
define([], function() {
    var Route = function($quiz) {
        this.$questions = $quiz.find(".question");
        this.pos = 0;

        this.skip = function(n) {
            this.pos += n;
            if (this.pos >= this.$questions.length) {
                this.pos = this.$questions.length - 1;
            } else if (this.pos < 0) {
                this.pos = 0;
            }
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

        this.next = function(scores) {
            var is_symbol = /^symbol_.*$/.test(id);
            var id = this.current_id();
            if(id == "symbol_1" && scores.has_score(id) && scores.H[id]) {
               this.skip(4);
            } else if(is_symbol && id != "symbol_4" && scores.has_score(id)) {
               this.skip(2); 
            } else {
               this.skip(1);
            }
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
            if(prev_id != "" && scores.has_score(prev_id)) {
                if (id=="symbol_2") {
                    this.skip(-4);
                }
                else {
                    this.skip(-2);
                }
                return
            }
            this.skip(-1);
        }
    };
    return Route;
});