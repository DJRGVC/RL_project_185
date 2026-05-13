---
audit_time: 04:12
figure: fig_morning_headline.png
script: agent_reports/make_fig_morning_headline.py
---

**Issue found:** The pre-registered kill-bar annotation was rendered as bright red inline text (`color="#c0392b"`, the label "HER + 0.10 KILL bar (PnP) = 0.27") floating over the FetchPickAndPlace cluster. This violated two NeurIPS conventions: (1) no verbose inline text annotations — contextual labels belong in captions, and (2) `#c0392b` is not in the CB-safe Tableau Color Blind 10 palette.

**Fix applied:** Removed the `ax.text(...)` call entirely. Converted the `ax.hlines(...)` call to use `colors="#595959"` (the same neutral dark gray already used for Path A Bidir) with `label="kill bar (PnP, HER+0.10)"` so the reference line now appears in the legend rather than as a floating annotation. The dashed line itself is retained — it encodes the pre-registered threshold and is scientifically necessary. The label in the legend gives readers enough context; full explanation will live in the caption.

**Result:** Figure is now NeurIPS-compliant. The kill-bar line reads as a reference mark, not a presentation callout. No data was altered; all bar heights, error bars, and seed dots are unchanged.
