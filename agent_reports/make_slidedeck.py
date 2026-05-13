"""Assemble the 9pm slidedeck PDF -- 16:9 landscape companion to the paper."""
from pathlib import Path
from reportlab.lib.pagesizes import landscape
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
OUT = REPORTS / "9pm_slidedeck.pdf"

# 16:9 landscape, 13.33 x 7.5 inch
PAGE_W = 13.33 * inch
PAGE_H = 7.5 * inch
PAGESIZE = (PAGE_W, PAGE_H)

# --- styles -----------------------------------------------------------
DARK    = HexColor("#1f2d3d")
ACCENT  = HexColor("#2c5d7d")
GREEN   = HexColor("#3aa66e")
ORANGE  = HexColor("#d99151")
RED     = HexColor("#c0392b")
GRAY    = HexColor("#566573")
LIGHT   = HexColor("#ecf2f6")
SOFTBG  = HexColor("#f6f9fb")

styles = getSampleStyleSheet()

TITLE = ParagraphStyle("Title", parent=styles["Heading1"],
                      fontName="Helvetica-Bold", fontSize=40, leading=46,
                      textColor=DARK, alignment=TA_CENTER, spaceAfter=18)
SUBTITLE = ParagraphStyle("SubTitle", parent=styles["Heading2"],
                      fontName="Helvetica", fontSize=22, leading=28,
                      textColor=ACCENT, alignment=TA_CENTER, spaceAfter=14)
AUTHORS = ParagraphStyle("Authors", parent=styles["BodyText"],
                      fontName="Helvetica", fontSize=22, leading=28,
                      textColor=DARK, alignment=TA_CENTER, spaceAfter=8)
TAG = ParagraphStyle("Tag", parent=styles["BodyText"],
                      fontName="Helvetica-Oblique", fontSize=20, leading=26,
                      textColor=GRAY, alignment=TA_CENTER, spaceAfter=4)
SLIDE_H = ParagraphStyle("SlideH", parent=styles["Heading1"],
                      fontName="Helvetica-Bold", fontSize=30, leading=36,
                      textColor=DARK, alignment=TA_LEFT, spaceAfter=12)
SLIDE_H_ITAL = ParagraphStyle("SlideHIta", parent=styles["Heading1"],
                      fontName="Helvetica-BoldOblique", fontSize=30, leading=36,
                      textColor=DARK, alignment=TA_LEFT, spaceAfter=12)
SECTION = ParagraphStyle("Section", parent=styles["Heading2"],
                      fontName="Helvetica-Bold", fontSize=22, leading=27,
                      textColor=ACCENT, alignment=TA_LEFT, spaceAfter=8)
BULLET = ParagraphStyle("Bullet", parent=styles["BodyText"],
                      fontName="Helvetica", fontSize=24, leading=32,
                      textColor=DARK, alignment=TA_LEFT,
                      leftIndent=22, bulletIndent=4, spaceAfter=8)
SMALL_BULLET = ParagraphStyle("SmallBullet", parent=styles["BodyText"],
                      fontName="Helvetica", fontSize=18, leading=24,
                      textColor=DARK, alignment=TA_LEFT,
                      leftIndent=22, bulletIndent=4, spaceAfter=6)
CAPTION = ParagraphStyle("Cap", parent=styles["BodyText"],
                      fontName="Helvetica-Oblique", fontSize=13, leading=16,
                      textColor=GRAY, alignment=TA_CENTER, spaceAfter=2)
META = ParagraphStyle("Meta", parent=styles["BodyText"],
                      fontName="Helvetica", fontSize=14, leading=18,
                      textColor=GRAY, alignment=TA_LEFT, spaceAfter=4)
FOOT = ParagraphStyle("Foot", parent=styles["BodyText"],
                      fontName="Helvetica", fontSize=11, leading=14,
                      textColor=GRAY, alignment=TA_CENTER, spaceAfter=0)
EQN = ParagraphStyle("Eqn", parent=styles["BodyText"],
                      fontName="Helvetica-Bold", fontSize=32, leading=44,
                      textColor=ACCENT, alignment=TA_CENTER, spaceAfter=14, spaceBefore=8)
RED_CALLOUT = ParagraphStyle("RedCallout", parent=styles["BodyText"],
                      fontName="Helvetica-Bold", fontSize=22, leading=28,
                      textColor=RED, alignment=TA_CENTER, spaceAfter=4,
                      borderColor=RED, borderWidth=2, borderPadding=10,
                      backColor=HexColor("#fdecea"))


def hr():
    return HRFlowable(width="100%", thickness=1.2, color=HexColor("#bfcad3"),
                      spaceBefore=4, spaceAfter=10)


def bullet(text, style=BULLET, color=DARK):
    return Paragraph(
        f'<font color="{color.hexval()}">&#9656;</font>&nbsp;&nbsp; {text}',
        style
    )


def img_flow(filename, w_in=11.0, caption=None):
    p = FIGS / filename
    with PILImage.open(p) as im:
        iw, ih = im.size
    target_w = w_in * inch
    target_h = target_w * (ih / iw)
    # cap height
    max_h = 5.0 * inch
    if target_h > max_h:
        target_h = max_h
        target_w = target_h * (iw / ih)
    flow = [Image(str(p), width=target_w, height=target_h, hAlign="CENTER")]
    if caption:
        flow.append(Spacer(1, 0.05 * inch))
        flow.append(Paragraph(caption, CAPTION))
    return KeepTogether(flow)


# Slide number / footer
def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(PAGE_W / 2.0, 0.30 * inch,
        f"VLM-Guided Failure Localization & Verified CF Hindsight  ·  Grant et al. (CS 285)  ·  Slide {doc.page}")
    canvas.restoreState()


# --- document ---------------------------------------------------------
doc = SimpleDocTemplate(
    str(OUT), pagesize=PAGESIZE,
    leftMargin=0.55 * inch, rightMargin=0.55 * inch,
    topMargin=0.55 * inch, bottomMargin=0.55 * inch,
    title="9pm Slidedeck -- VLM-Guided Failure Localization (companion)",
    author="Daniel Grant",
)

story = []

# =====================================================================
# SLIDE 1 -- Title
# =====================================================================
story += [
    Spacer(1, 0.7 * inch),
    Paragraph("VLM-Guided Failure Localization", TITLE),
    Paragraph("and Verified Counterfactual Hindsight", TITLE),
    Spacer(1, 0.1 * inch),
    Paragraph("for Sparse-Reward Manipulation", SUBTITLE),
    Spacer(1, 0.35 * inch),
    Paragraph("Daniel Grant &nbsp;&middot;&nbsp; Parshawn Gerafian &nbsp;&middot;&nbsp; Matei Gardea", AUTHORS),
    Paragraph("CS 285 &nbsp;&middot;&nbsp; UC Berkeley &nbsp;&middot;&nbsp; Spring 2026", AUTHORS),
    Spacer(1, 0.4 * inch),
    Paragraph("A failure-direction, per-timestep, IS-grounded alternative to VLM-RB.", TAG),
]
story.append(PageBreak())

# =====================================================================
# SLIDE 2 -- Problem statement
# =====================================================================
story += [
    Paragraph("Problem statement", SLIDE_H),
    hr(),
    Spacer(1, 0.2 * inch),
    bullet("Sparse-reward goal-conditioned RL on Fetch (<b>Push, PickAndPlace, Slide</b>) &mdash; "
           "reward fires only on success."),
    bullet("Algorithm: <b>SAC + replay buffer</b>. Standard credit-assignment tools "
           "(TD-error PER, HER) treat all transitions as opaque."),
    bullet("Core question: <b>which transitions deserve more replay weight?</b> "
           "We propose: the ones the VLM identifies as the <i>cause of failure</i>."),
]
story.append(PageBreak())

# =====================================================================
# SLIDE 3 -- Concurrent work + differentiation
# =====================================================================
story += [
    Paragraph("Concurrent work &mdash; Sharony et&nbsp;al. (Feb 2026, NVIDIA + Technion)", SLIDE_H),
    hr(),
    Spacer(1, 0.1 * inch),
    bullet("<b>VLM-RB (arXiv:2602.01915):</b> frozen VLM scores 32-frame sub-trajectory clips for "
           "<i>goal satisfaction</i> &mdash; success direction.", style=BULLET),
    bullet("<b>Mixture-with-uniform</b> at sampling: &lambda;<sub>t</sub>&middot;&mu;<sub>VLM</sub> + "
           "(1&minus;&lambda;<sub>t</sub>)&middot;&mu;<sub>U</sub>. Requires &lambda; warm-up.",
           style=BULLET),
    bullet("Evaluated on <b>MiniGrid + OGBench</b>. No Fetch / Gymnasium-Robotics. No oracle baseline.",
           style=BULLET),
    bullet("Reports 11&ndash;52% success gain, 19&ndash;45% sample-efficiency gain over PER/UER.", style=BULLET),
    Spacer(1, 0.2 * inch),
    Paragraph("THREE MONTHS AHEAD OF US. WE MUST DIFFERENTIATE.", RED_CALLOUT),
]
story.append(PageBreak())

# =====================================================================
# SLIDE 4 -- Our two-track approach (split layout via Table)
# =====================================================================
# Slightly smaller bullet style just for this split layout
SPLIT_BULLET = ParagraphStyle("SplitBullet", parent=SMALL_BULLET,
                              fontSize=16, leading=20,
                              leftIndent=14, bulletIndent=2, spaceAfter=5)
SPLIT_SECTION = ParagraphStyle("SplitSection", parent=SECTION,
                               fontSize=20, leading=24, spaceAfter=8)

path_a_para = [
    Paragraph("<b>Path A &mdash; Failure-Direction PER</b>", SPLIT_SECTION),
    Paragraph("&#9656;&nbsp; <b>Semantic PER:</b> VLM localizes failure timestep; PER priority gets multiplicative window boost.", SPLIT_BULLET),
    Paragraph("&#9656;&nbsp; <b>Oracle v3</b> (contact-aware): ballistic &rarr; contact-loss &rarr; argmin; decouples mechanism from VLM accuracy.", SPLIT_BULLET),
    Paragraph("&#9656;&nbsp; <b>Bidirectional buffer:</b> success_weight &times; failure_weight; degenerates to PER when both are 1.", SPLIT_BULLET),
    Paragraph("&#9656;&nbsp; <b>HER baseline sweep</b> (27 jobs on Modal, overnight).", SPLIT_BULLET),
]
path_c_para = [
    Paragraph("<b>Path C &mdash; Verified Counterfactual Hindsight</b>", SPLIT_SECTION),
    Paragraph("&#9656;&nbsp; <b>Counterfactual VLM:</b> at failure timestep, ask <i>what action should the agent have taken?</i>", SPLIT_BULLET),
    Paragraph("&#9656;&nbsp; <b>Verified-CF (N1):</b> roll VLM's action in a sim fork; accept only if env's own sparse reward fires.", SPLIT_BULLET),
    Paragraph("&#9656;&nbsp; <b>Relabel</b> with confidence 1.0 (env signed off). Teleport collapse structurally inexpressible.", SPLIT_BULLET),
    Paragraph("&#9656;&nbsp; <b>Smoke:</b> 4/4 PASS, 17.6 ms per verification.", SPLIT_BULLET),
]
col_w = (PAGE_W - 1.1 * inch) / 2.0 - 0.15 * inch
split = Table(
    [[path_a_para, path_c_para]],
    colWidths=[col_w, col_w],
    rowHeights=[5.0 * inch],
)
split.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BOX", (0, 0), (0, 0), 1.2, ACCENT),
    ("BOX", (1, 0), (1, 0), 1.2, ORANGE),
    ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ("TOPPADDING", (0, 0), (-1, -1), 10),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ("BACKGROUND", (0, 0), (0, 0), SOFTBG),
    ("BACKGROUND", (1, 0), (1, 0), HexColor("#fff7ed")),
]))
story += [
    Paragraph("Our 2-track approach", SLIDE_H),
    hr(),
    split,
]
story.append(PageBreak())

# =====================================================================
# SLIDE 5 -- Headline result
# =====================================================================
HEADLINE_BULLET = ParagraphStyle("HeadlineBullet", parent=SMALL_BULLET,
                                 fontSize=15, leading=20, spaceAfter=4,
                                 leftIndent=10, bulletIndent=2)
story += [
    Paragraph("Headline result &mdash; overnight Path C kill experiment", SLIDE_H),
    hr(),
    img_flow("fig_morning_headline.png", w_in=10.5,
             caption="Final eval success rate at 250k steps. HER vs Oracle-CF "
                     "(pre-fix and post-fix Push) vs Path A Bidir. n=3 seeds for HER/OCF, "
                     "n=2 for Bidir. Pre-registered HER+0.10 KILL bar drawn on PnP."),
    Spacer(1, 0.04 * inch),
    Paragraph(
        "&#9656;&nbsp; <b>KILL.</b> &Delta;(OCF&minus;HER) on FetchPickAndPlace = "
        "<b>&minus;0.05</b> &mdash; well below the +0.10 pre-registered threshold. "
        "Post-fix Push &Delta; = &minus;0.17. Path A Bidir 5/6 = 0.0. "
        "<i>HER on Fetch is at the credit-assignment ceiling; bottleneck is exploration, not credit.</i>",
        HEADLINE_BULLET,
    ),
]
story.append(PageBreak())

# =====================================================================
# SLIDE 6 -- Theoretical motivation (N3)
# =====================================================================
story += [
    Paragraph("Theoretical motivation (N3): Semantic PER as IS posterior reweighting", SLIDE_H),
    hr(),
    Spacer(1, 0.15 * inch),
    Paragraph("&mu;<sub>Sem</sub>(i) &nbsp;&prop;&nbsp; &mu;<sub>P</sub>(i) &nbsp;&middot;&nbsp; w<sub>sem</sub>(i;&nbsp;&tau;)", EQN),
    Paragraph(
        "where w<sub>sem</sub>(i;&nbsp;&tau;) = E<sub>t* &sim; q<sub>&phi;</sub></sub>[ K<sub>W</sub>(i;&nbsp;t*) ] &mdash; "
        "VLM is the proposal q<sub>&phi;</sub>(t* | &tau;); priority factorises into learning-progress &times; causal-influence.",
        CAPTION),
    Spacer(1, 0.2 * inch),
    bullet("<b>No &lambda; warm-up:</b> multiplicative weight degenerates to PER cleanly when w<sub>sem</sub> = 1.",
           style=SMALL_BULLET),
    bullet("<b>Single hyperparam</b> (w<sub>max</sub>) vs Sharony's mixture schedule.", style=SMALL_BULLET),
    bullet("<b>Principled ablations:</b> ESS of w<sub>sem</sub>; KL(p<sub>oracle</sub> || q<sub>&phi;</sub>); "
           "IS-correction variants &mdash; diagnostics Sharony's recipe cannot produce.", style=SMALL_BULLET),
    bullet("<b>Reframes the paper:</b> from <i>&quot;VLM-PER beats PER by X%&quot;</i> to "
           "<i>&quot;foundation-model priors as credit-assignment oracles&quot;</i> &mdash; a thesis, not a benchmark.",
           style=SMALL_BULLET),
]
story.append(PageBreak())

# =====================================================================
# SLIDE 7 -- Verifiable counterfactuals (N1)
# =====================================================================
# We don't have a dedicated diagram, so use a prose-diagram via Table
diagram_cells = [
    [Paragraph("<b>1. VLM</b>", SECTION),
     Paragraph("<b>2. Sim fork</b>", SECTION),
     Paragraph("<b>3. Reward check</b>", SECTION),
     Paragraph("<b>4. Buffer</b>", SECTION)],
    [Paragraph("Propose corrective<br/>action at s<sub>K</sub>", SMALL_BULLET),
     Paragraph("Restore qpos / qvel /<br/>mocap to s<sub>K</sub>; roll 50 steps", SMALL_BULLET),
     Paragraph("Env's <b>own sparse<br/>reward</b> fires? &rarr; accept", SMALL_BULLET),
     Paragraph("Relabel with confidence 1.0;<br/>HER fallback on reject", SMALL_BULLET)],
]
cw = (PAGE_W - 1.1 * inch) / 4.0 - 0.05 * inch
diagram = Table(diagram_cells, colWidths=[cw] * 4, rowHeights=[0.55 * inch, 1.5 * inch])
diagram.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("BOX", (0, 0), (-1, -1), 1, ACCENT),
    ("INNERGRID", (0, 0), (-1, -1), 1, ACCENT),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ("BACKGROUND", (0, 0), (-1, 0), SOFTBG),
]))

story += [
    Paragraph("Verifiable counterfactuals (N1) &mdash; closes the teleport-collapse loophole", SLIDE_H),
    hr(),
    diagram,
    Spacer(1, 0.18 * inch),
    bullet("<b>Teleport is structurally inexpressible</b> as a 4-vector action &mdash; failure mode eliminated by construction.",
           style=SMALL_BULLET),
    bullet("<b>Off-policy correctness:</b> value function trains on the <i>real</i> sparse reward, "
           "not a VLM surrogate. Reward shaping doesn't get this guarantee.", style=SMALL_BULLET),
    bullet("<b>Smoke test (N1_smoke_results.json):</b> 4/4 PASS, 17.6 ms per verification, ~0.4% wall-clock overhead.",
           style=SMALL_BULLET),
    bullet("<b>Buffer integration:</b> ~50 LOC subclassing C2's CounterfactualHERBuffer stub.",
           style=SMALL_BULLET),
]
story.append(PageBreak())

# =====================================================================
# SLIDE 8 -- Cross-task transferability (N2)
# =====================================================================
N2_BULLET = ParagraphStyle("N2Bullet", parent=SMALL_BULLET,
                           fontSize=15, leading=20, spaceAfter=4,
                           leftIndent=10, bulletIndent=2)
story += [
    Paragraph("Cross-task transferability (N2)", SLIDE_H),
    hr(),
    img_flow("figN2_cross_task_transfer.png", w_in=8.5,
             caption="VLM keyframe-agreement with heuristic oracle. Same prompt, three envs. "
                     "Claude Opus 4.7, K=5 keyframes, 4 episodes/env."),
    Spacer(1, 0.02 * inch),
    bullet("<b>12/12 task-relevant</b> annotations across Push, PickAndPlace, Slide &mdash; "
           "<i>one prompt template, three envs, no retraining.</i>", style=N2_BULLET),
    bullet("<b>Sharony cannot make this claim</b> &mdash; their architecture trains per benchmark "
           "(DQN/IQN on MiniGrid; SAC/TD3 on OGBench).", style=N2_BULLET),
]
story.append(PageBreak())

# =====================================================================
# SLIDE 9 -- Honest publishability claim
# =====================================================================
story += [
    Paragraph("Honest publishability claim (post-overnight)", SLIDE_H_ITAL),
    hr(),
    Spacer(1, 0.1 * inch),
    bullet("<b>We have:</b> IS-posterior <i>framing</i> (&sect;3), verifier <i>mechanism</i> (&sect;4 / N1), "
           "cross-task <i>signal</i> (N2: 12/12 task-relevant), and a <b>pre-registered, falsified</b> "
           "Path C kill experiment &mdash; a real negative result, not noise.",
           style=SMALL_BULLET, color=GREEN),
    bullet("<b>We don't have:</b> a positive empirical headline on Fetch. Privileged Oracle-CF "
           "did not beat HER by 0.10 on any env; Path A Bidir 5/6 = 0.0; Phase 2 Modal sweep "
           "never fired (A1's HER sweep holding GPUs).",
           style=SMALL_BULLET, color=ORANGE),
    bullet("<b>Recommended path:</b> reframe as &lsquo;methodology + theory + honest negative empirical&rsquo; "
           "NeurIPS submission; scale N2 to n=50/env locally; let Phase 2 land as &sect;5 ablation when Modal frees. "
           "Do not pivot to harder envs now &mdash; 4 days of training is a bet we cannot underwrite.",
           style=SMALL_BULLET, color=ACCENT),
    bullet("<b>Realistic submission:</b> NeurIPS main track with negative-result framing OR "
           "NeurIPS workshop on Robot Learning as defensive fallback.", style=SMALL_BULLET, color=DARK),
]
story.append(PageBreak())

# =====================================================================
# SLIDE 10 -- What I did tonight
# =====================================================================
story += [
    Paragraph("What got done overnight (22:00 &rarr; 10:00 PDT)", SLIDE_H),
    hr(),
    bullet("<b>Path C kill experiment</b> ran to completion: 22 runs at 250k steps. "
           "&Delta;(OCF&minus;HER) PnP = &minus;0.05 &rarr; <b>KILL verdict</b>.",
           style=SMALL_BULLET, color=RED),
    bullet("<b>oracle_cf_push midpoint bug</b> identified and fixed (<i>ccb63d4</i>); "
           "3-seed rerun: mean 0.383 vs HER 0.550 &mdash; verdict held.",
           style=SMALL_BULLET, color=ORANGE),
    bullet("<b>Watchdog pivot fired</b> at 03:02 PDT; Path A bidir relaunch debugged "
           "(<i>eb899be</i>: missing config + wrong CLI form); 6 runs ran 03:33&ndash;06:01.",
           style=SMALL_BULLET),
    bullet("<b>Path A Bidir result</b>: 5/6 = 0.0 success; only Push s42 = 0.4 at 300k. Bidir does not save Path A.",
           style=SMALL_BULLET, color=ORANGE),
    bullet("<b>Paper edits:</b> &sect;3 R2 honesty pass (<i>d2ce20b</i>); &sect;6 Broader Impact "
           "restructured (<i>c488c6b</i>); uniqueness claim dropped; bias bound added (<i>95d9cee</i>).",
           style=SMALL_BULLET),
    bullet("<b>Phase 2 Modal blocked all night</b>: A1's HER sweep holding all 10 GPU slots; "
           "watchdog correctly never auto-launched.",
           style=SMALL_BULLET, color=GRAY),
    bullet("<b>Crons stalled ~03:53 PDT</b> when LLM session lapsed; bash watchdog stayed alive but "
           "couldn't compensate. Morning consolidation crons (06:33-07:36) missed.",
           style=SMALL_BULLET, color=GRAY),
]
story.append(PageBreak())

# =====================================================================
# SLIDE 11 -- Next steps
# =====================================================================
story += [
    Paragraph("Next steps &mdash; three options for Daniel to choose", SLIDE_H),
    hr(),
    bullet("<b>(a) Pivot to harder envs (Adroit / MetaWorld / AntMaze).</b> "
           "18 runs, ~4 days wallclock. P(at least one OCF beats HER) &asymp; 50%. "
           "Risk: 4 of 5 remaining days consumed.", style=SMALL_BULLET, color=RED),
    bullet("<b>(b) Reframe as methodology + theory + honest negative result paper.</b> "
           "No new training. 4 days for rewrite. Mitigation: workshop fallback.",
           style=SMALL_BULLET, color=GREEN),
    bullet("<b>(c) Scale N2 (n=12 &rarr; n=50/env) + run Verified-CF Phase 2 when Modal frees.</b> "
           "1 day local + 18h Phase 2. Phase 2 inherits Path C's empirical weakness.",
           style=SMALL_BULLET, color=ACCENT),
    Spacer(1, 0.1 * inch),
    bullet("<b>Recommendation: (b) + a defensive slice of (c).</b> Reframe paper around IS-posterior + "
           "verifier + honest kill result. Scale N2 locally. Let Phase 2 land when Modal frees as "
           "&sect;5 ablation. Do <b>not</b> pursue (a) right now &mdash; calendar is too tight.",
           style=SMALL_BULLET, color=DARK),
    Spacer(1, 0.05 * inch),
    bullet("<b>Pre-Phase-2 must-fix:</b> <i>modal_app.py</i> WANDB_ENTITY regression "
           "(_CODE_BLOCKER.md B2) &mdash; every Phase 2 job will crash at wandb.init otherwise.",
           style=SMALL_BULLET, color=ORANGE),
]

# Build
doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
print(f"wrote {OUT}")
