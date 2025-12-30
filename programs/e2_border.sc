# SemioCore v1.0 — Paper Demo E2: border contextuality witness
context Add(0.5) >> Sign {
  tick 1.0;
  u1 := sense chN;
  commit u1;

  do add_bias(0.0);
  tick 1.0;
  u2 := sense chN;
  commit u2;
}
out := summarize;
