# Phase 2 VLM Launch — FAILURE ALERT

**Detected:** 2026-05-12 10:27 PDT (17:27 UTC)
**Agent:** training-status-check (Sonnet 4.6)

---

## Summary

Phase 2 (Verified-CF / VLM-augmented) Modal runs launched successfully at 2026-05-11 22:20 PDT
but ALL 11 runs that appeared in W&B crashed within 6–26 seconds. 5 of 18 expected runs
never appeared in W&B at all (crashed before W&B init).

A new Modal app (`ap-bLMnC0sqx6kVCe7oAERWUQ`, 10 tasks) appeared at 10:27 PDT —
possibly an automatic retry or second launch attempt.

---

## Evidence

### Crash signature (from W&B run summaries)
- `buffer/cf_vlm_returned_none > 0` — VLM returns None (not an exception)
- `buffer/cf_vlm_exceptions = 0` — no Python exception raised, silent None return
- `buffer/cf_relabel_count = 0` — zero VLM-based relabeling ever occurred
- Runtime: 6–26 seconds before `finished` state

### Tag issue
Runs were tagged with per-job tags (e.g. `path_c_vlm_cf_pp`) but NOT the expected
umbrella tag `path_c_vlm_2026-05-12`. W&B queries for that tag return 0 results.

### Missing runs (5 of 18 never appeared in W&B)
- path_c_vlm_vcf_pp_s42_seed42
- path_c_vlm_vcf_pp_s123_seed123
- path_c_vlm_vcf_pp_s999_seed999
- path_c_vlm_vcf_sld_s123_seed123
- path_c_vlm_vcf_sld_s999_seed999

---

## Likely Root Cause

**VLM API credentials not injected into Modal containers.**

The VLM client returns None (not an exception) when called — this matches the behavior
of a stub or a client that silently fails due to missing API key. The `cf_vlm_exceptions=0`
rules out a Python-level crash; the None return is the actual response.

Action needed:
1. Check Modal secret configuration for the VLM API key (OpenAI/Anthropic/other)
2. Verify the Modal app's `secrets=` list includes the VLM credential secret
3. Add a startup assertion in the train script: `assert VLM_API_KEY is not None`
4. Re-tag relaunched runs with `path_c_vlm_2026-05-12` umbrella tag

---

## Current Modal State

| App ID | Description | State | Tasks | Created |
|--------|-------------|-------|-------|---------|
| ap-bLMnC0sqx6kVCe7oAERWUQ | semantic-p... | ephemeral (detached) | 10 | 10:27 PDT 5/12 |
| ap-dzTbfB1VPzyhx73lN1Jles | semantic-p... | stopped | 0 | 10:26 PDT 5/12 |
| ap-OCyr832mvzGOvjyePo9qjP | semantic-p... | stopped | 0 | 10:25 PDT 5/12 |
| ap-PWMTBsinFWdaAK048ySfBV | semantic-p... | stopped | 0 | 22:20 PDT 5/11 |
