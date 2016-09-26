        
define([], function() {
        var Scores = function() {
            this.S = {};
            this.E = {};
            this.H = {};
            this.update = function(name, vals) {
                this.S[name] = vals[0];
                this.H[name] = vals[1];
                this.E[name] = vals[2];
                //console.debug("Updated "+name+":");
                //console.debug(this.pretty(name));
            }

            this.reset = function() {
                this.S = {};
                this.H = {};
                this.E = {};
            };

            this.score = function(name, cb) {
                var cum_scores = this;
                return function(val) {
                    var scores = cb(val);
                    if(!scores) {
                        scores = [0, 0, 0];
                    }
                    cum_scores.update(name, scores);
                };
            };

            this.pretty = function(q_id) {
                var sc = this;
                var render = function(k) {
                    return k +": S" + sc.S[k] + "H: " + sc.H[k] + "E: " + sc.E[k]+"\n";
                }
                if(q_id) {
                    return render(q_id);
                }
                var out = "";
                for(var k in this.S) {
                    out += render(k);
                }
                return out;
            }

            this.has_score = function(name) {
                if((name in this.S && this.S[name]) || 
                   (name in this.E && this.E[name]) || 
                   (name in this.H && this.H[name])) {

                    return true;
                }
                else {
                    return false;
                }
            }

            this.get_S = function() {
                var cS = 0;
                for (var k in this.S) {
                    cS += this.S[k];
                }
                return cS;
            };

            var get_band = function(val) {
                if (val < 4) {
                    return "good";
                } else if (val > 6) {
                    return "bad";
                } else {
                    return "ok";
                }                
            }

            this.get_S_band = function() {
                return get_band(this.get_S());
            }
            
            this.get_H = function() {
                var cH = this.H['boiling_point'];
                var max = 0;
                for (var k in this.H) {
                    if (k != "boiling_point") {
                        var t = this.H[k];
                        if (t > max) {
                            max = t;
                        }
                    }
                }
                return cH + max;
            };
            this.get_H_band = function() {
                return get_band(this.get_H());
            };


            this.get_E = function() {
                var cE = 0;
                for (var k in this.E) {
                    var t = this.E[k];
                    if (t > cE) {
                        cE = t;
                    }
                }
                return cE;
            };

            this.get_E_band = function() {
                return get_band(this.get_E());
            };


            this.get_default_ranking = function() {
                var normalise = function(val) {
                    if (val > 7) {
                        return 6;
                    } else if (val > 6) {
                        return 3;
                    } else if (val > 3) {
                        return 1;
                    } else {
                        return 0;
                    }
                };

                var nS = normalise(this.get_S());
                var nH = normalise(this.get_H());
                var nE = normalise(this.get_E());
                
                var sum = nS + nH + nE;
                if (sum > 5) {
                    return "Hazardous";
                } else if (sum > 1) {
                    return "Problematic";
                } else {
                    return "Recommended";
                }
            };

            this.get_default_ranking_band = function() {
                var ranking = this.get_default_ranking();
                switch(ranking) {
                    case "Hazardous":
                        return "bad";
                    case "Problematic":
                        return "ok";
                    case "Recommended":
                        return "good";
                }
            };

            this.boiling_point = this.score("boiling_point", function(val) {
                // H: =IF(B2<=85,1,0)
                var H = 0;
                var E = 0;
                if(val <= 85) {
                    H = 1;
                }
                // E: =IF(B2<50,7,IF(B2<70,5,IF(B2<140,3,IF(B2<=200,5,7))))
                if(val < 50) {
                    E = 7;
                } else if(val < 70) {
                    E = 5;
                } else if(val < 140) {
                    E = 3;
                } else if(val <= 200) {
                    E = 5;
                } else {
                    E = 7;
                }
                return [0, H, E];
            });
            this.flash_point = this.score("flash_point", function(val) {
                var S = 0;
                if(val < -20) {
                    S = 7;
                } else if(val < 0) {
                    S = 5;
                } else if(val < 23) {
                    S = 4;
                } else if(val <=60) {
                    S = 3;
                } else {
                    S = 1;
                }
                return [S, 0, 0];
            });
            this.AIT = this.score("AIT", function(val) {
                if(val < 200) {
                    return [1, 0, 0]; 
                }
            });
            var res_cb = function(val) {
                if(val) {
                    return [1, 0, 0];
                }
            };

            var res_cb_2 = function(val) {
                if(!val) {
                    return [1, 0, 0];
                }
            };

            this.resistivity = this.score("resistivity", res_cb);
            this.resistivity_2 = this.score("resistivity_2", res_cb_2);
            this.ether_explosive_peroxide = this.score("ether_explosive_peroxide", res_cb);

            var symbol_cb = function(val) {
                if(!val) {
                    return [0, 1, 0];
                }
            };

            this.symbol_1 = this.score("symbol_1", symbol_cb);
            this.symbol_2 = this.score("symbol_2", symbol_cb);
            this.symbol_3 = this.score("symbol_3", symbol_cb);

            this.symbol_4 = this.score("symbol_4", function(val) {
                if(val) {
                    return [0,2,0];
                } else {
                    return [0,1,0];
                }
            });


            this.symbol_5 = this.score("symbol_5", function(val) {
                if(!val) {
                    return [0,0,1];
                }
            });

            this.h340 = this.score("h340", function(val) {
                    if(val) {
                        return [0, 9, 0];
                    } else {
                        return [0, 2, 0];
                    }
            });

            this.h341 = this.score("h341", function(val) {
                    if(val) {
                        return [0, 6, 0];
                    } else {
                        return [0, 2, 0];
                    }
            });

            this.h370 = this.score("h370", function(val) {
                if(val) {
                    return [0, 6, 0];
                } else {
                    return [0, 2, 0];
                }
            });

            this.h334 = this.score("h334", function(val) {
                    if(val) {
                        return [0, 4, 0];
                    } else {
                        return [0, 2, 0];
                    }
            });

            this.h300 = this.score("h300", function(val) {
                    if(val) {
                        return [0, 9, 0];
                    } else {
                        return [0, 6, 0];
                    }
            });

            this.h314 = this.score("h314", function(val) {
                    if(val) {
                        return [0, 7, 0];
                    } else {
                        return [0, 4, 0];
                    }
            });

            this.ozone = this.score("ozone", function(val) {
                    if(val) {
                        return [0, 0, 10];
                    } else {
                        return [0, 0, 1];
                    }
            });

            this.h400 = this.score("h400", function(val) {
                    if(val) {
                        return [0, 0, 7];
                    } else {
                        return [0, 0, 5];
                    }
            });

            this.reach = this.score("reach", function(val) {
                if(val) {
                    return [0, 1, 1];
                } else {
                    return [0, 5, 5];
                }
            });

        };
        return Scores;

});