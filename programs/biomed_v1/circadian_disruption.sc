# Circadian disruption regime (SemioCore biomed contract)
context Add(0.10) >> Sign {
  tick 1.0;
  u := sense chCircadianScore;
  commit u;
}
out := summarize;
