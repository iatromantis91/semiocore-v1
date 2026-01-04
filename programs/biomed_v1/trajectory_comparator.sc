# Trajectory comparator regime (SemioCore biomed contract)
context Sign {
  tick 1.0;
  pre := sense chTrajectoryPre;
  commit pre;

  tick 1.0;
  post := sense chTrajectoryPost;
  commit post;
}
out := summarize;
