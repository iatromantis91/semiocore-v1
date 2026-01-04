# Metabolic risk regime (SemioCore biomed contract)
context Add(-0.15) >> Sign {
  tick 1.0;
  u := sense chMetabolicScore;
  commit u;
}
out := summarize;
