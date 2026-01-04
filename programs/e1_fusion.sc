# SemioCore v1.0 — Paper Demo E1: affine fusion (Add composition)
context Add(0.2) >> Add(0.3) {
  tick 1.0;
  u1 := sense chP;
  commit u1;

  do add_bias(0.0);
  tick 1.0;
  u2 := sense chQ;
  commit u2;
}
out := summarize;
