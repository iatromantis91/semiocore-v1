SHELL := /bin/bash
PY := python3

WORLD := fixtures/world/paper_world.json
OUT := out

# Ignore runtime-only manifest fields + hashes (tooling may canonicalize hashing differently)
IGNORE_MANIFEST := run_id,timestamp,program_hash_sha256,world_hash_sha256

.PHONY: paper-demo clean dirs check run compare e1-opt e2-ctx e3-replay paper-figures

paper-demo: clean dirs check run compare e1-opt e2-ctx e3-replay paper-figures
	@echo "paper-demo: ALL CHECKS PASSED"

clean:
	rm -rf $(OUT)

dirs:
	mkdir -p $(OUT)

check:
	semioc check --strict programs/e1_fusion.sc
	semioc check --strict programs/e2_border.sc
	semioc check --strict programs/e3_jitter_seed.sc

run:
	semioc run programs/e1_fusion.sc --world $(WORLD) \
	  --emit-manifest $(OUT)/e1.manifest.json \
	  --emit-trace $(OUT)/e1.trace.json

	semioc run programs/e2_border.sc --world $(WORLD) \
	  --emit-manifest $(OUT)/e2.manifest.json \
	  --emit-trace $(OUT)/e2.trace.json

	semioc run programs/e3_jitter_seed.sc --world $(WORLD) \
	  --emit-manifest $(OUT)/e3.manifest.json \
	  --emit-trace $(OUT)/e3.trace.json

compare:
	$(PY) tools/compare_json.py fixtures/expected/e1.manifest.json $(OUT)/e1.manifest.json --ignore $(IGNORE_MANIFEST)
	$(PY) tools/compare_json.py fixtures/expected/e2.manifest.json $(OUT)/e2.manifest.json --ignore $(IGNORE_MANIFEST)
	$(PY) tools/compare_json.py fixtures/expected/e3.manifest.json $(OUT)/e3.manifest.json --ignore $(IGNORE_MANIFEST)

	$(PY) tools/compare_trace.py fixtures/expected/e1.trace.json $(OUT)/e1.trace.json
	$(PY) tools/compare_trace.py fixtures/expected/e2.trace.json $(OUT)/e2.trace.json
	$(PY) tools/compare_trace.py fixtures/expected/e3.trace.json $(OUT)/e3.trace.json

e1-opt:
	semioc opt programs/e1_fusion.sc --emit-core $(OUT)/e1_optimized.sc --emit-proof $(OUT)/e1_opt_proof.json
	semioc verify-proof $(OUT)/e1_opt_proof.json
	semioc run $(OUT)/e1_optimized.sc --world $(WORLD) --emit-trace $(OUT)/e1_optimized.trace.json
	$(PY) tools/compare_trace.py $(OUT)/e1.trace.json $(OUT)/e1_optimized.trace.json

e2-ctx:
	semioc ctxscan programs/e2_border.sc --world $(WORLD) --window 2 \
	  --emit-report $(OUT)/e2.ctxreport.json \
	  --emit-permuted-trace $(OUT)/e2.permuted.trace.json

	semioc ctxwitness --operators "Add(0.5),Sign" --projection "threshold@0" --emit $(OUT)/e2.witness.json

	$(PY) tools/compare_json.py fixtures/expected/e2.ctxreport.json $(OUT)/e2.ctxreport.json --tol 1e-9
	$(PY) tools/compare_trace.py fixtures/expected/e2.permuted.trace.json $(OUT)/e2.permuted.trace.json
	$(PY) tools/compare_json.py fixtures/expected/e2.witness.json $(OUT)/e2.witness.json --tol 1e-9

e3-replay:
	semioc replay --trace $(OUT)/e3.trace.json --manifest $(OUT)/e3.manifest.json --emit-trace $(OUT)/e3.replay.trace.json
	$(PY) tools/compare_trace.py fixtures/expected/e3.replay.trace.json $(OUT)/e3.replay.trace.json

paper-figures:
	mkdir -p $(OUT)/paper_figures
	$(PY) paper_figures/make_tables.py \
	  --outdir $(OUT)/paper_figures \
	  --e1 $(OUT)/e1.trace.json \
	  --e2 $(OUT)/e2.trace.json \
	  --e2p $(OUT)/e2.permuted.trace.json \
	  --e3 $(OUT)/e3.trace.json \
	  --ctxreport $(OUT)/e2.ctxreport.json

	$(PY) paper_figures/make_figures.py \
	  --outdir $(OUT)/paper_figures \
	  --e1 $(OUT)/e1.trace.json \
	  --e2 $(OUT)/e2.trace.json \
	  --e2p $(OUT)/e2.permuted.trace.json \
	  --e3 $(OUT)/e3.trace.json

	$(PY) paper_figures/make_cite_snippets.py \
	  --out $(OUT)/paper_figures/cite_snippets.md \
	  --runs_csv $(OUT)/paper_figures/table_runs.csv \
	  --ctx_csv $(OUT)/paper_figures/table_ctxreport.csv \
	  --figdir $(OUT)/paper_figures

.PHONY: paper-demo paper-demo-run paper-demo-replay paper-demo-ctxscan paper-demo-compare

paper-demo: paper-demo-run paper-demo-replay paper-demo-ctxscan paper-demo-compare
	@echo "OK: paper-demo"

paper-demo-run:
	@mkdir -p out
	py -3 -m semioc run programs/e1_fusion.sc --world fixtures/world/paper_world.json --emit-manifest out/e1.manifest.json --emit-trace out/e1.trace.json
	py -3 -m semioc run programs/e2_border.sc --world fixtures/world/paper_world.json --emit-manifest out/e2.manifest.json --emit-trace out/e2.trace.json
	py -3 -m semioc run programs/e3_jitter_seed.sc --world fixtures/world/paper_world.json --emit-manifest out/e3.manifest.json --emit-trace out/e3.trace.json

paper-demo-replay:
	@mkdir -p out
	py -3 -m semioc replay --manifest fixtures/expected/e3.manifest.json --emit-trace out/e3.replay.trace.json

paper-demo-ctxscan:
	@mkdir -p out
	py -3 -m semioc ctxscan programs/e1_fusion.sc --world fixtures/world/paper_world.json --emit-report out/e1.ctxscan.json
	py -3 -m semioc ctxscan programs/e2_border.sc --world fixtures/world/paper_world.json --emit-report out/e2.ctxscan.json
	py -3 -m semioc ctxscan programs/e3_jitter_seed.sc --world fixtures/world/paper_world.json --emit-report out/e3.ctxscan.json

paper-demo-compare:
	py -3 tools/compare_trace.py fixtures/expected/e1.trace.json out/e1.trace.json
	py -3 tools/compare_trace.py fixtures/expected/e2.trace.json out/e2.trace.json
	py -3 tools/compare_trace.py fixtures/expected/e3.trace.json out/e3.trace.json
	py -3 tools/compare_trace.py fixtures/expected/e3.replay.trace.json out/e3.replay.trace.json
	py -3 tools/compare_json.py fixtures/expected/e1.ctxscan.json out/e1.ctxscan.json
	py -3 tools/compare_json.py fixtures/expected/e2.ctxscan.json out/e2.ctxscan.json
	py -3 tools/compare_json.py fixtures/expected/e3.ctxscan.json out/e3.ctxscan.json
