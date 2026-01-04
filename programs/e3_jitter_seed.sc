# SemioCore v1.0 — Paper Demo E3: reproducible pseudo-stochastic jitter (seeded)
seed 12345;
context JitterU(0.05) {
  tick 1.0;
  u1 := sense chS;
  commit u1;

  do add_bias(0.0);
  tick 1.0;
  u2 := sense chS;
  commit u2;
}
out := summarize;
