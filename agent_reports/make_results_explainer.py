"""Assemble agent_reports/results_explainer.pdf -- Daniel-facing status
briefing on RL_project_185 CF-VLM-PER results so far, honest assessment.

Companion to methods_explainer.pdf. ~6-7 pages.
"""
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether
)
from PIL import Image as PILImage

ROOT = Path("/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185")
REPORTS = ROOT / "agent_reports"
FIGS = REPORTS / "figs"
OUT = REPORTS / "results_explainer.pdf"

# Colors (match methods_explainer)
DARK   = HexColor("#1C2630")
ACCENT = HexColor("#0173B2")
GREEN  = HexColor("#029E73")
ORANGE = HexColor("#DE8F05")
RED    = HexColor("#CC3311")
PURPLE = HexColor("#9F2B68")
GRAY   = HexColor("#56575A")
LIGHT  = HexColor("#ECEEF1")
INK    = HexColor("#22313F")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"],
                   fontName="Helvetica-Bold", fontSize=18, leading=22,
                   textColor=DARK, spaceAfter=6, spaceBefore=0)
H2 = ParagraphStyle("H2", parent=styles["Heading2"],
                   fontName="Helvetica-Bold", fontSize=13, leading=16,
                   textColor=ACCENT, spaceAfter=4, spaceBefore=10)
H3 = ParagraphStyle("H3", parent=styles["Heading3"],
                   fontName="Helvetica-Bold", fontSize=11, leading=14,
                   textColor=DARK, spaceAfter=2, spaceBefore=6)
BODY = ParagraphStyle("Body", parent=styles["BodyText"],
                     fontName="Helvetica", fontSize=10, leading=14,
                     textColor=INK, spaceAfter=4, alignment=TA_LEFT)
BODYJ = ParagraphStyle("BodyJ", parent=BODY, alignment=TA_JUSTIFY)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=9, leading=12,
                       textColor=HexColor("#3A4A59"), spaceAfter=2)
CAPTION = ParagraphStyle("Cap", parent=BODY, fontSize=8.5, leading=11,
                         textColor=GRAY, alignment=TA_CENTER, spaceAfter=2)
META = ParagraphStyle("Meta", parent=BODY, fontSize=9, leading=12,
                     textColor=GRAY, spaceAfter=2, alignment=TA_LEFT)
NOTE = ParagraphStyle("Note", parent=BODY, fontSize=9.5, leading=13,
                      textColor=DARK, leftIndent=10, spaceAfter=3)
TIGHT = ParagraphStyle("Tight", parent=BODY, fontSize=9.5, leading=12.5,
                       spaceAfter=3, alignment=TA_JUSTIFY)
CALLOUT = ParagraphStyle("Callout", parent=BODY, fontSize=10, leading=13.5,
                         textColor=DARK, spaceAfter=4, leftIndent=8,
                         rightIndent=8)


def hr():
    return HRFlowable(width="100%", thickness=0.7, color=HexColor("#BFCAD3"),
                      spaceBefore=2, spaceAfter=6)


def img(name, w=7.0, caption=None):
    p = FIGS / name
    with PILImage.open(p) as im:
        iw, ih = im.size
    target_w = w * inch
    target_h = target_w * (ih / iw)
    flow = [Image(str(p), width=target_w, height=target_h)]
    if caption:
        flow.append(Spacer(1, 0.04 * inch))
        flow.append(Paragraph(caption, CAPTION))
    return KeepTogether(flow)


def bullet(text, color=DARK):
    return Paragraph(
        f'<font color="{color.hexval()}">&#9656;</font>&nbsp; {text}',
        NOTE,
    )


def banner(text, bg_color, fg_color=DARK):
    return Table(
        [[Paragraph(f'<font color="{fg_color.hexval()}">{text}</font>',
                    ParagraphStyle("BN", parent=BODY, fontSize=10.5,
                                   leading=14, alignment=TA_LEFT,
                                   fontName="Helvetica-Bold"))]],
        colWidths=[7.2 * inch],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ]),
    )


# --- document ---------------------------------------------------------
doc = SimpleDocTemplate(
    str(OUT), pagesize=LETTER,
    leftMargin=0.65*inch, rightMargin=0.65*inch,
    topMargin=0.55*inch, bottomMargin=0.55*inch,
    title="Results Explainer: where RL_project_185 stands",
    author="Daniel Grant",
)

story = []

# =====================================================================
# PAGE 1 -- TL;DR
# =====================================================================
story += [
    Paragraph("Results Explainer &mdash; where we stand", H1),
    Paragraph(
        "Honest status briefing on the CF-VLM-PER project. "
        "Companion to methods_explainer.pdf. &nbsp;&middot;&nbsp; "
        "Daniel Grant, CS 285 final project, May 12, 2026.",
        META,
    ),
    hr(),

    Paragraph("TL;DR (4-6 bullets)", H2),
    bullet(
        "<b>Pre-registered kill verdict at 250k: FAILED.</b> Oracle-CF lost "
        "to HER by &Delta;=&minus;0.05 on PnP and &Delta;=&minus;0.23 on Push "
        "(corrected). The verdict was documented and respected.",
        RED),
    bullet(
        "<b>Oracle-CF at 1M (in progress): mean 0.60 across 2 seeds</b> "
        "(s42=0.30, s123=0.90). Huge variance. 3rd seed (s999) running now, "
        "ETA tomorrow. Without HER@1M comparator, we cannot say \"we beat HER.\"",
        ORANGE),
    bullet(
        "<b>Phase 2 VLM-CF on Push shows real climb:</b> SR 0.45&ndash;0.50 "
        "at 215&ndash;238k of the 500k target. The non-verified VLM-CF "
        "mechanism has some signal even without the headline verification gate.",
        GREEN),
    bullet(
        "<b>Verified-CF mechanism (the headline novelty): 100% verifier "
        "rejection at 143k on PnP.</b> Cold-start regime persists longer than "
        "expected. This is the load-bearing experiment and it is not working yet.",
        RED),
    bullet(
        "<b>Sharony VLM-RB baseline:</b> implemented but not yet run; ready "
        "to launch when GPU frees.",
        GRAY),
    bullet(
        "<b>AntMaze pivot:</b> fully planned (ANTMAZE_PIVOT_PLAN.md); not "
        "yet implemented. ~5 days of work if we commit.",
        GRAY),

    Spacer(1, 0.10 * inch),
    banner(
        "Where we stand: ~20-25% NeurIPS main-track confidence, ~80% workshop confidence.",
        HexColor("#FFF3E0"), fg_color=HexColor("#7A4A00"),
    ),
    Spacer(1, 0.08 * inch),

    Paragraph("What this document is", H2),
    Paragraph(
        "A six-page snapshot of what our experiments have actually shown so "
        "far, with calibrated confidence in each component of the paper. The "
        "tone is the inverse of the paper draft: no spin, no hopeful framing. "
        "If something is broken, this document says it is broken. If "
        "something is uncertain, this document says it is uncertain.",
        BODYJ),
    Paragraph(
        "Use it to (a) decide whether to keep pushing Fetch, pivot to "
        "AntMaze, or run both in parallel; (b) brief collaborators in 90 "
        "seconds; (c) sanity-check the paper draft against what we actually "
        "know.",
        BODYJ),
]

story.append(PageBreak())

# =====================================================================
# PAGE 2 -- Timeline
# =====================================================================
story += [
    Paragraph("Visual timeline &mdash; what we ran, what came back", H1),
    Paragraph(
        "Chronological view of the day's experiments, color-coded by outcome. "
        "Green = positive signal, yellow = mixed / high variance, red = negative "
        "result, gray = ready but not yet run.",
        BODY),
    hr(),

    img("results_explainer_timeline.png", w=7.2,
        caption="Each event on the axis is a separate experiment family. The two earliest "
                "phases (Phase 1 kill, Path A bidir pivot) gave clear negative verdicts. The "
                "afternoon's Oracle-CF 1M runs are climbing but with seed-level variance. The "
                "Push column of Phase 2 attempt 5 is the one unambiguously positive signal. "
                "Verified-CF on PnP is the explicit failure."),

    Spacer(1, 0.10 * inch),
    Paragraph("Three things the timeline shows", H2),
    bullet(
        "<b>Lots of red early in the day, more nuance later.</b> The 250k kill "
        "horizon eliminated the bold claim (\"Oracle-CF beats HER at 250k\"). "
        "Everything after that is either an extension to longer training or a "
        "different mechanism.",
        DARK),
    bullet(
        "<b>The only green block is non-verified VLM-CF on Push.</b> That is "
        "<i>not</i> the headline mechanism &mdash; it is the simpler ablation. "
        "The headline mechanism (Verified-CF) is the red block in the evening.",
        DARK),
    bullet(
        "<b>The yellow block (Oracle-CF 1M) is the most consequential.</b> "
        "If the 3rd seed lands near 0.60 and HER@1M lands meaningfully below "
        "that, we have a clean empirical result. If the 3rd seed lands near "
        "0.30, or HER@1M matches us, we do not.",
        DARK),
]

story.append(PageBreak())

# =====================================================================
# PAGE 3 -- Verified-CF mechanism diagram
# =====================================================================
story += [
    Paragraph("The CF-VLM-PER mechanism, visually", H1),
    Paragraph(
        "Verified-CF is the contribution the paper hangs on. The diagram below "
        "shows what the agent does at a failed timestep, and where the "
        "current training run is getting stuck.",
        BODY),
    hr(),

    img("results_explainer_mechanism.png", w=7.0,
        caption="The four-step pipeline: VLM proposes a corrective action; we snapshot the "
                "simulator at the failure timestep; we roll out the VLM's action in a fork; "
                "we accept the proposed transition only if the env's own reward fires. "
                "Accepted transitions go into the PER buffer at high priority. Rejected "
                "transitions are silently discarded &mdash; the agent gets no learning signal "
                "from them. This is the gate that makes the imagined CF transitions "
                "physically valid by construction."),

    Spacer(1, 0.08 * inch),
    Paragraph("Why we expected this to work", H2),
    Paragraph(
        "Plain CF-HER (the version without the verification gate) can quietly "
        "lie. The VLM proposes an imagined goal G*, we relabel, and if the "
        "trajectory never actually reached G* the recomputed reward is still "
        "0 &mdash; or worse, if the relabel happens at the achieved state, the "
        "reward fires for a state the agent did not actually drive to. We "
        "called this the <i>teleport pathology</i> in the methods explainer.",
        BODYJ),
    Paragraph(
        "Verified-CF eliminates teleports by construction: nothing enters the "
        "buffer unless the simulator confirms reward = 1 from the proposed "
        "action. The unit-test pass rate (4/4 on the smoke suite) confirms "
        "the mechanism behaves correctly in isolation.",
        BODYJ),

    Paragraph("Why it is failing right now", H2),
    Paragraph(
        "On PnP at 143k steps, <b>every single CF attempt is rejected</b>. "
        "The VLM proposes 101 corrective actions, all 101 fail the verifier "
        "(reward never fires). The buffer never gets a verified CF transition, "
        "so the agent learns nothing from CF, and PER falls back to vanilla "
        "TD-error priorities &mdash; which is also approximately zero in cold-start.",
        BODYJ),
    Paragraph(
        "Two hypotheses, both live: (a) the early-training policy is so far "
        "from the manifold of successful behaviour that no 1-step VLM correction "
        "can recover &mdash; in which case a warm-started variant (pre-train with "
        "HER, then turn on Verified-CF) might work; or (b) the mechanism is "
        "fundamentally a bad fit for Fetch's continuous-control action space. "
        "We cannot distinguish these without the warm-start experiment.",
        BODYJ),
]

story.append(PageBreak())

# =====================================================================
# PAGE 4 -- Honest results breakdown
# =====================================================================
story += [
    Paragraph("Honest results breakdown", H1),
    Paragraph(
        "Two horizons, two stories. The 250k panel is the pre-registered kill "
        "horizon (left). The 1M panel is the target horizon, mostly still in "
        "flight (right).",
        BODY),
    hr(),

    img("results_explainer_bars.png", w=7.2,
        caption="Left: at the 250k kill horizon, the Oracle-CF mechanism underperforms HER "
                "and is far below PER. The kill verdict was registered here. "
                "Right: at the 1M target horizon, Oracle-CF has climbed substantially "
                "(seed mean 0.60), but the two finished seeds disagree by 0.60 in absolute SR "
                "&mdash; one of the largest seed variances we have seen. HER@1M has not "
                "been run yet, which is the load-bearing comparator we still need."),

    Spacer(1, 0.06 * inch),
    Paragraph("Interpretation, plain English", H2),

    Paragraph(
        "<b>Oracle-CF at 1M is climbing.</b> The mean of 0.60 across two seeds "
        "is dramatically higher than the 250k-step Oracle-CF number (0.133), "
        "and it is above the 250k HER reference (0.183). That is encouraging. "
        "But seed 42 finished at 0.30 and seed 123 finished at 0.90 &mdash; a "
        "0.60 absolute gap. That is not a result we can confidently report "
        "without at least a third seed (running now, ETA tomorrow morning), "
        "and ideally a fourth. And without HER@1M as a comparator, we cannot "
        "make the claim \"Oracle-CF beats HER at 1M\" &mdash; we can only say "
        "\"Oracle-CF improves over its own 250k baseline.\"",
        BODYJ),

    Paragraph(
        "<b>VLM-CF (non-verified) on Push shows real mid-training climb.</b> "
        "At 215&ndash;238k of the 500k training budget, seeds 42 and 999 are at "
        "SR 0.50 and 0.45 respectively. Seed 123 is lagging at 0.10. This is "
        "the <i>non-verified</i> VLM-CF mechanism &mdash; the ablation, not the "
        "headline. The fact that it shows signal on Push without the "
        "verification gate suggests the VLM proposals on Push are good enough "
        "that the sim-rollout filter would be largely a no-op there. If that "
        "holds at 500k it is a useful positive secondary result, but it does "
        "not validate the verification gate itself.",
        BODYJ),

    Paragraph(
        "<b>Verified-CF (the headline) is currently broken on PnP.</b> 100% "
        "verifier rejection at 143k means the buffer never receives a single "
        "Verified-CF transition, so the mechanism is effectively a no-op. "
        "Either (a) the cold-start failure mode is the only barrier and a "
        "warm-started variant (HER pre-training, then turn on Verified-CF) "
        "would work, or (b) the mechanism just does not work on Fetch PnP. "
        "We need the warm-start retry to know which. Until we do, the paper's "
        "headline empirical claim has no supporting training data on its "
        "primary task.",
        BODYJ),
]

story.append(PageBreak())

# =====================================================================
# PAGE 5 -- Hopefulness scorecard
# =====================================================================
story += [
    Paragraph("Hopefulness scorecard, per contribution", H1),
    Paragraph(
        "Each row is a contribution we could plausibly claim in the paper. "
        "The right column is honest confidence that the contribution survives "
        "scrutiny &mdash; not optimism, not hedging.",
        BODY),
    hr(),
]


def conf_cell(level):
    color_map = {
        "HIGH":         (GREEN,  "HIGH"),
        "MEDIUM-HIGH":  (GREEN,  "MED&ndash;HIGH"),
        "MEDIUM":       (ORANGE, "MEDIUM"),
        "LOW-MEDIUM":   (ORANGE, "LOW&ndash;MED"),
        "LOW":          (RED,    "LOW"),
        "UNCERTAIN":    (PURPLE, "UNCERTAIN"),
    }
    color, label = color_map[level]
    return Paragraph(
        f'<para align="center"><font color="{color.hexval()}" size="9"><b>{label}</b></font></para>',
        ParagraphStyle("Conf", parent=BODY, alignment=TA_CENTER),
    )


def text_cell(text, size=8.5, color=INK, bold=False):
    style_name = "TC"
    weight_tag_open = "<b>" if bold else ""
    weight_tag_close = "</b>" if bold else ""
    return Paragraph(
        f'<font size="{size}" color="{color.hexval()}">{weight_tag_open}{text}{weight_tag_close}</font>',
        ParagraphStyle(style_name, parent=BODY, fontSize=size,
                       leading=size + 2.5, textColor=color),
    )


scorecard_rows = [
    [
        text_cell("Theory: IS-posterior framing + bias bound", bold=True),
        text_cell("39-page paper, reviewers' Top-3 (R1 & R2) addressed in two iter rounds"),
        conf_cell("HIGH"),
        text_cell("Stands regardless of training. Lemma + bound are proven; "
                  "reviewer-2 theory-skeptic feedback was incorporated.",
                  size=8, color=GRAY),
    ],
    [
        text_cell("Verified-CF mechanism (the headline)", bold=True),
        text_cell("4/4 unit-test pass; failing in training (100% reject @ 143k on PnP)"),
        conf_cell("LOW-MEDIUM"),
        text_cell("Needs warm-start retry OR positive Push@500k to recover. "
                  "Currently the weakest leg of the paper.",
                  size=8, color=GRAY),
    ],
    [
        text_cell("Semantic PER (Path A, failure-direction)", bold=True),
        text_cell("Oracle 0.417 &gt; PER 0.383 (small win); GPT-4o 0.306 (loss vs PER)"),
        conf_cell("MEDIUM"),
        text_cell("Workable positive secondary result. The VLM is the "
                  "bottleneck, not the mechanism.",
                  size=8, color=GRAY),
    ],
    [
        text_cell("Cross-task transferability claim (N2)", bold=True),
        text_cell("12/12 task-relevant counterfactuals from N2 study; not yet at scale"),
        conf_cell("MEDIUM"),
        text_cell("Would be MED&ndash;HIGH if scaled to n=50. "
                  "Currently pilot-sized.",
                  size=8, color=GRAY),
    ],
    [
        text_cell("Sharony reproduction baseline", bold=True),
        text_cell("Implemented (L1_sharony_differentiation.md); not yet run"),
        conf_cell("HIGH"),
        text_cell("HIGH for methodology section once run. Reproduces "
                  "their VLM-RB to position our method clearly.",
                  size=8, color=GRAY),
    ],
    [
        text_cell("Empirical Fetch result vs HER", bold=True),
        text_cell("Pending Oracle-CF 1M completion + HER@1M run"),
        conf_cell("UNCERTAIN"),
        text_cell("Load-bearing for the headline. Without it the paper is "
                  "theory + ablations, not a comparison.",
                  size=8, color=GRAY),
    ],
]

# Header
header_cells = [
    text_cell("Contribution", size=9, bold=True, color=DARK),
    text_cell("What we have", size=9, bold=True, color=DARK),
    Paragraph('<para align="center"><font size="9" color="#1C2630"><b>Confidence</b></font></para>',
              ParagraphStyle("ConfH", parent=BODY, alignment=TA_CENTER)),
    text_cell("Notes", size=9, bold=True, color=DARK),
]
scorecard_data = [header_cells] + scorecard_rows
col_widths = [1.65*inch, 2.10*inch, 0.95*inch, 2.45*inch]
sc_tbl = Table(scorecard_data, colWidths=col_widths, repeatRows=1)
sc_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E5EEF5")),
    ("LINEABOVE", (0, 0), (-1, 0), 0.6, GRAY),
    ("LINEBELOW", (0, 0), (-1, 0), 0.6, GRAY),
    ("LINEBELOW", (0, -1), (-1, -1), 0.6, GRAY),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
     [HexColor("#FFFFFF"), HexColor("#F7F9FB")]),
]))
story.append(sc_tbl)

story += [
    Spacer(1, 0.10 * inch),
    Paragraph(
        "<b>How to read this:</b> the paper survives reviewing if the HIGH-row "
        "items hold up, the MEDIUM rows are positioned as secondary, and the "
        "UNCERTAIN row gets cleared in the next 48 hours. The LOW&ndash;MED "
        "row (Verified-CF) is the one where we still need a positive training "
        "signal. The most fragile sentence in the current paper draft is the "
        "one claiming Verified-CF works empirically; everything else is "
        "defensible.",
        BODYJ),
    Spacer(1, 0.04 * inch),
    img("results_explainer_push_climb.png", w=6.5,
        caption="Phase 2 attempt 5 VLM-CF (non-verified) on Push. Lines are a sketch through "
                "checkpoint anchors (0/50k/100k/150k/200k/238k); seed 42 and seed 999 are "
                "tracking together, seed 123 is stuck. Half of the 500k budget remains."),
]

story.append(PageBreak())

# =====================================================================
# PAGE 6 -- Three paths forward
# =====================================================================
story += [
    Paragraph("Three paths forward &mdash; decision aid", H1),
    Paragraph(
        "Each path is honestly priced. The Hybrid option (C) is what this "
        "document suggests, but the call is Daniel's.",
        BODY),
    hr(),

    img("results_explainer_paths.png", w=7.2,
        caption="Three resource-allocation choices. A is conservative and uses existing infra. "
                "B is the cleaner-theory option but burns most of the remaining time on infra. "
                "C splits attention to keep both options open through Thursday."),

    Spacer(1, 0.08 * inch),
    Paragraph("Path A &mdash; Stick with Fetch, run HER@1M + verified-CF warm-start retry", H3),
    Paragraph(
        "<b>What it costs:</b> ~2 days. <b>What it produces:</b> a clean "
        "HER@1M vs Oracle-CF@1M comparison (the load-bearing empirical "
        "claim), plus one shot at making Verified-CF work via warm-start. "
        "<b>Honest probable outcome:</b> we end up with a clean comparison "
        "vs HER. The Verified-CF retry may or may not succeed. If HER@1M "
        "lands above 0.60, the headline empirical claim collapses. If it "
        "lands below 0.60 and our s999 confirms the mean, we have a "
        "publishable result.",
        TIGHT),

    Paragraph("Path B &mdash; Pivot to AntMaze", H3),
    Paragraph(
        "<b>What it costs:</b> ~5 days (1.5&ndash;2 days infrastructure + "
        "2&ndash;3 days training). <b>What it produces:</b> Oracle-CF on "
        "AntMaze has the BFS-geodesic property &mdash; the oracle's "
        "counterfactual is provably the shortest-path correction, which is "
        "strictly cleaner than Fetch's heuristic oracle. The theory section "
        "is a tighter fit. <b>Honest probable outcome:</b> if the training "
        "lands clean, this is a stronger paper than Fetch. If it does not "
        "land, we have burned 5 of our remaining days and have to retreat to "
        "Fetch with less of it left.",
        TIGHT),

    Paragraph("Path C &mdash; Hybrid (suggested)", H3),
    Paragraph(
        "<b>What it costs:</b> ~2 days for A + start B's infra in parallel. "
        "<b>What it produces:</b> by Thursday we have a Fetch HER@1M "
        "comparator <i>and</i> AntMaze first runs underway. Either result "
        "can carry the paper. <b>Honest probable outcome:</b> we keep "
        "options open through the most uncertain phase. Cost is thinner "
        "attention on each. Recommended.",
        TIGHT),

    Spacer(1, 0.12 * inch),
    hr(),
    banner(
        "Bottom line: we have a solid methodology paper. The headline empirical claim is "
        "uncertain &mdash; and that is the whole game right now.",
        HexColor("#E8F4F0"), fg_color=HexColor("#0B4A38"),
    ),
    Spacer(1, 0.06 * inch),
    Paragraph(
        "If you read nothing else: the theory and methods sections are in "
        "good shape. The Fetch experiment that backs the headline is in "
        "flight and we will not know its full verdict for ~24 hours. The "
        "Verified-CF mechanism itself works in unit tests but is currently "
        "blocked in training on PnP. Until either the warm-start retry "
        "succeeds, Push@500k lands cleanly, or AntMaze first-runs come back "
        "positive, the safest framing of the paper is \"theory + Path A "
        "secondary result\" rather than \"Verified-CF beats HER.\"",
        BODYJ),
]

doc.build(story)
print(f"wrote {OUT}")
