# Inflammation proxy regime (SemioCore biomed contract)
context Sign {
  tick 1.0;
  u := sense chInflamScore;
  commit u;
}
out := summarize;
