# Quality-control regime (SemioCore biomed contract)
context Sign {
  tick 1.0;
  u := sense chQCFlag;
  commit u;
}
out := summarize;
