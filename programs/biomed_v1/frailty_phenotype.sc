# Frailty-style phenotype regime (SemioCore biomed contract)
context Add(-0.05) >> Sign {
  tick 1.0;
  u := sense chFrailtyScore;
  commit u;
}
out := summarize;
