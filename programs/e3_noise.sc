# E3: noise/jitter — requires seed
seed 123;

context Add(0.2)>>JitterU(0.1)>>Add(0.3) {
  tick 1.0;
  x := sense chP;
  commit x;

  tick 1.0;
  y := sense chQ;
  commit y;

  out := summarize;
}
