"""Assemble agent_reports/methods_explainer.pdf -- educational explainer
of the replay-buffer family (UER -> PER -> Semantic PER -> HER -> CF-HER ->
Verified-CF).

Audience: ML engineer new to this RL subfield. ~6 pages, visual, friendly.
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
OUT = REPORTS / "methods_explainer.pdf"

# Colors
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
CODE = ParagraphStyle("Code", parent=BODY, fontName="Courier",
                      fontSize=9, leading=11.5, textColor=INK,
                      backColor=LIGHT, leftIndent=8, rightIndent=8,
                      borderPadding=6, spaceAfter=4, spaceBefore=2)
NOTE = ParagraphStyle("Note", parent=BODY, fontSize=9.5, leading=13,
                      textColor=DARK, leftIndent=10, spaceAfter=3)


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


# --- document ---------------------------------------------------------
doc = SimpleDocTemplate(
    str(OUT), pagesize=LETTER,
    leftMargin=0.65*inch, rightMargin=0.65*inch,
    topMargin=0.55*inch, bottomMargin=0.55*inch,
    title="Replay-Buffer Methods: A Visual Explainer",
    author="Daniel Grant",
)

story = []

# =====================================================================
# PAGE 1 -- The problem
# =====================================================================
story += [
    Paragraph("Replay-Buffer Methods, a Visual Explainer", H1),
    Paragraph(
        "From uniform replay to verified counterfactuals &mdash; "
        "the family tree behind RL_project_185. &nbsp;&middot;&nbsp; "
        "Daniel Grant, CS 285, May 2026.",
        META,
    ),
    hr(),

    Paragraph("The problem we are trying to solve", H2),
    Paragraph(
        "A robot tries to do a task. It mostly fails. We want it to learn "
        "from those failures. To do that, every step of every attempt gets "
        "stuffed into a big bucket called the <b>replay buffer</b>, and "
        "stochastic gradient descent pulls samples out and uses them to "
        "improve the policy.",
        BODYJ),
    Paragraph(
        "Two things make this hard. First, the reward is <b>sparse</b>: "
        "the robot sees a 0 for almost every transition and only finds out "
        "whether it succeeded at the very last step. Second, even when the "
        "episode <i>does</i> finish with a 1, we have no idea <b>which</b> "
        "of the 50 transitions in that episode actually deserves credit. "
        "This is the <b>credit assignment problem</b>, and it is what every "
        "method on the next pages is attacking.",
        BODYJ),

    Spacer(1, 0.08 * inch),
    img("explainer_problem.png", w=6.8,
        caption="Every episode produces a strip of transitions (s, a, r, s'). "
                "Only the last one carries a non-zero reward. The buffer collects them all; "
                "SGD has to figure out which ones are worth learning from."),
]

story.append(PageBreak())

# =====================================================================
# PAGE 2 -- Family tree
# =====================================================================
story += [
    Paragraph("The family tree", H1),
    Paragraph(
        "Six methods, all answering the same question (\"which transitions "
        "should we sample, and with what reward?\") in increasingly clever "
        "ways. The branches in green are this project's contributions.",
        BODY),

    hr(),
    img("explainer_family_tree.png", w=7.0,
        caption="Each leaf method is a different bet about how to fix the credit-assignment "
                "problem. UER bets on \"all transitions matter the same.\" PER bets on "
                "\"surprising transitions matter more.\" HER bets on \"if we missed the goal, "
                "pretend we meant to land where we did.\" The leaves below them refine these bets "
                "using a vision-language model (VLM)."),

    Spacer(1, 0.06 * inch),
    Paragraph("One-line intuition for each", H2),
    bullet(
        "<b>UER</b> (Uniform Experience Replay): sample any transition with "
        "equal probability. Boring but unbiased &mdash; the baseline.",
        GRAY),
    bullet(
        "<b>PER</b> (Prioritized Experience Replay, Schaul 2016): sample "
        "transitions where the agent is most <i>surprised</i> (high TD-error) "
        "more often. \"Learn from your mistakes.\"",
        ACCENT),
    bullet(
        "<b>HER</b> (Hindsight Experience Replay, Andrychowicz 2017): when "
        "the agent fails, relabel the goal to be wherever the agent <i>actually</i> "
        "ended up. Now every episode is a success at <i>something</i>.",
        ORANGE),
    bullet(
        "<b>Semantic PER</b> (this project, Path A): ask a vision-language "
        "model where the failure happened, then up-weight the transitions "
        "around that timestep on top of PER.",
        GREEN),
    bullet(
        "<b>Counterfactual HER</b> (CF-HER): ask the VLM \"if you were going "
        "to succeed, what should the goal have been?\" Use the VLM's answer "
        "as the relabel goal.",
        ORANGE),
    bullet(
        "<b>Verified-CF</b> (this project, Path C, agent N1): same as CF-HER, "
        "but only accept the VLM's proposal if it actually works when "
        "replayed in the simulator. \"Trust but verify.\"",
        RED),
]

story.append(PageBreak())

# =====================================================================
# PAGE 3 -- Side-by-side comparison table
# =====================================================================
story += [
    Paragraph("Side-by-side comparison", H1),
    Paragraph(
        "All six methods in one table. Read the rows top-to-bottom &mdash; "
        "each row builds on the previous one.",
        BODY),
    hr(),
]

# Define table rows
TABLE_HEADER = ["Method", "What it does", "When it helps", "When it hurts",
                "Key knob", "Published example"]
TABLE_ROWS = [
    [
        "<b>UER</b>",
        "Sample transitions uniformly at random.",
        "Always safe baseline; cheap; unbiased.",
        "Wastes capacity on transitions the agent already understands.",
        "(none)",
        "Mnih et al. 2015 (DQN on Atari)",
    ],
    [
        "<b>PER</b>",
        "Sample with probability proportional to |TD-error|<sup>&alpha;</sup>.",
        "Dense rewards or any setting where TD-error is informative.",
        "Sparse-reward tasks: TD-error is ~0 everywhere until the goal.",
        "&alpha; (priority sharpness), &beta; (IS correction)",
        "Schaul et al. 2016 (Prioritized Replay, DQN Atari)",
    ],
    [
        "<b>HER</b>",
        "On failed episodes, relabel goal = achieved state; recompute reward.",
        "Goal-conditioned manipulation with sparse rewards.",
        "Tasks without a clear achieved-goal representation; can confuse the policy if the relabel goal is unreachable from earlier states.",
        "k (number of relabels per episode), strategy (\"future\", \"final\")",
        "Andrychowicz et al. 2017 (Fetch tasks)",
    ],
    [
        "<b>Semantic PER</b>",
        "Multiply PER priority by a VLM-derived failure-window weight.",
        "Long-horizon tasks where one transition is causally responsible for failure.",
        "Tasks where the VLM cannot identify the failure frame; flat trajectories.",
        "W (window radius), w_max (boost magnitude)",
        "This project (Fetch, 1M steps); Sharony et al. 2026 (MiniGrid, OGBench)",
    ],
    [
        "<b>CF-HER</b>",
        "VLM proposes a counterfactual goal G*; relabel and recompute reward.",
        "Cases where the policy was \"close to right\" and the VLM can verbalize the near-miss.",
        "If the trajectory never reached G*, reward is still 0 -- no winning transition is created. Mechanistic weakness.",
        "p_counterfactual (frequency of CF relabels)",
        "This project, Path C v1 (synthetic + real Fetch failures)",
    ],
    [
        "<b>Verified-CF</b>",
        "VLM proposes a corrective action; sim is rolled out; accept only if env reward fires.",
        "Whenever the simulator is cheap to fork; turns the VLM into a generator of provably-valid transitions.",
        "Needs a forkable simulator. VLM still has to produce a coherent action sequence.",
        "rollout horizon, accept threshold",
        "This project, Path C v2 (agent N1, 4/4 smoke pass)",
    ],
]

def cell(text, size=8.5, color=INK):
    return Paragraph(
        f'<font size="{size}" color="{color.hexval()}">{text}</font>',
        ParagraphStyle("Cell", parent=BODY, fontSize=size, leading=size+2.5,
                       textColor=color, alignment=TA_LEFT),
    )

header_cells = [cell(h, size=9, color=DARK) for h in TABLE_HEADER]
table_data = [header_cells]
for row in TABLE_ROWS:
    table_data.append([cell(c) for c in row])

col_widths = [0.80*inch, 1.45*inch, 1.30*inch, 1.45*inch, 0.95*inch, 1.35*inch]
tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E5EEF5")),
    ("LINEABOVE", (0, 0), (-1, 0), 0.6, GRAY),
    ("LINEBELOW", (0, 0), (-1, 0), 0.6, GRAY),
    ("LINEBELOW", (0, -1), (-1, -1), 0.6, GRAY),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#F7F9FB")]),
]))

story.append(tbl)

story += [
    Spacer(1, 0.08 * inch),
    Paragraph(
        "<b>How to read this table:</b> each method fixes a specific weakness of "
        "the previous one. UER -&gt; PER fixes \"every transition treated equally.\" "
        "PER -&gt; HER fixes \"TD-error is zero in sparse-reward land.\" "
        "HER -&gt; Semantic PER fixes \"HER only relabels the achieved goal, "
        "it does not tell you which timestep mattered.\" "
        "Semantic PER -&gt; CF-HER changes the question from \"which transition?\" "
        "to \"which goal?\" "
        "CF-HER -&gt; Verified-CF fixes \"the VLM's imagined goal might be a lie.\"",
        BODYJ),
]

story.append(PageBreak())

# =====================================================================
# PAGE 4 -- Pseudocode side-by-side (the easy ones)
# =====================================================================
story += [
    Paragraph("Pseudocode &mdash; the easy three", H1),
    Paragraph(
        "These three you can implement in an afternoon. Read them as templates: "
        "the later methods (Semantic PER, CF-HER, Verified-CF) are <i>extensions</i> "
        "of these three, not replacements.",
        BODY),
    hr(),

    Paragraph("UER &mdash; Uniform Experience Replay", H3),
    Paragraph(
        "Pull a random transition with equal probability. That is the whole algorithm.",
        SMALL),
    Paragraph(
        "i = uniform_random(0, len(buffer))<br/>"
        "transition = buffer[i]",
        CODE),

    Spacer(1, 0.05 * inch),
    Paragraph("PER &mdash; Prioritized Experience Replay", H3),
    Paragraph(
        "Each transition i has a priority p_i = |TD-error_i|<sup>&alpha;</sup>. "
        "Pull it proportional to its priority. Re-weight the gradient with an "
        "importance-sampling correction so that the loss is still unbiased.",
        SMALL),
    Paragraph(
        "p_i = (|TD_i| + eps) ** alpha<br/>"
        "i ~ Categorical(p_i / sum_j p_j)<br/>"
        "w_i = ((N * p_i / sum_j p_j) ** -beta) / max_w&nbsp;&nbsp;# IS correction<br/>"
        "loss = w_i * (Q(s_i,a_i) - target_i) ** 2",
        CODE),

    Spacer(1, 0.05 * inch),
    Paragraph("HER &mdash; Hindsight Experience Replay", H3),
    Paragraph(
        "On a failed episode tau, pick a future state, relabel the goal to "
        "be that state's achieved_goal, recompute the reward function on the "
        "relabeled trajectory, and push the relabeled transitions back into "
        "the buffer.",
        SMALL),
    Paragraph(
        "for tau in failed_episodes:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;for t in range(len(tau)):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# pick a future timestep t' &gt; t<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;t_prime = random_future(t, len(tau))<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;new_goal = tau[t_prime].achieved_goal<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;new_reward = env.compute_reward(tau[t].achieved_goal, new_goal)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;buffer.push(tau[t] with desired_goal=new_goal, reward=new_reward)",
        CODE),

    Spacer(1, 0.08 * inch),
    Paragraph(
        "<b>Mental model:</b> UER is the bucket. PER is a smarter way to pull "
        "from the bucket. HER is a way to <i>add more useful things to the bucket</i>. "
        "PER and HER are orthogonal &mdash; you can do both. (Most modern manipulation "
        "papers do.)",
        BODYJ),
]

story.append(PageBreak())

# =====================================================================
# PAGE 5 -- The novel ones, with diagrams
# =====================================================================
story += [
    Paragraph("The novel three, with diagrams", H1),
    Paragraph(
        "All three add a vision-language model (VLM) to the loop. They differ "
        "in <i>what they ask the VLM to produce</i>, and how much they trust the answer.",
        BODY),
    hr(),

    Paragraph("Semantic PER &mdash; \"which timestep was the mistake?\"", H3),
    Paragraph(
        "Show the VLM keyframes from the episode and ask it to point to the "
        "<b>critical failure timestep t*</b>. Build a soft window of radius W "
        "around t* and multiply each transition's PER priority by that window. "
        "Transitions near the mistake get sampled much more often.",
        BODY),

    img("explainer_semantic_per.png", w=5.8,
        caption="The VLM picks the critical moment; we boost a small window around it. "
                "Outside the window, behaviour is identical to vanilla PER."),

    Spacer(1, 0.04 * inch),
    Paragraph("Counterfactual HER &mdash; \"what should the goal have been?\"", H3),
    Paragraph(
        "Instead of asking about timesteps, ask the VLM about <b>goals</b>. "
        "On a failed episode the VLM proposes an imagined goal G*; we relabel "
        "desired_goal = G* and recompute the reward, exactly like HER.",
        BODY),

    img("explainer_cf_her.png", w=5.6,
        caption="CF-HER swaps real goal G for VLM-imagined G*. Honest weakness: "
                "if the trajectory never reached G*, the recomputed reward is still 0."),

    Spacer(1, 0.03 * inch),
    Paragraph("Verified-CF &mdash; \"prove your counterfactual works\"", H3),
    Paragraph(
        "The fix. Ask the VLM for a <b>corrective action sequence</b>, snapshot "
        "the simulator at the failure timestep, roll out the VLM's action in a "
        "forked sim, and accept only if the environment's own reward fires. "
        "Accepted transitions are guaranteed physically valid with a real reward of 1.",
        BODYJ),

    img("explainer_verified_cf.png", w=6.2,
        caption="Verified-CF gates VLM proposals through the simulator. "
                "Teleport pathologies are eliminated by construction."),
]

story.append(PageBreak())

# =====================================================================
# PAGE 6 -- Why each method beats the previous (and when)
# =====================================================================
TIGHT = ParagraphStyle("Tight", parent=BODY, fontSize=9.5, leading=12.5,
                       spaceAfter=3, alignment=TA_JUSTIFY)
TIGHT_H = ParagraphStyle("TightH", parent=H3, fontSize=10.5, leading=13,
                         spaceAfter=1, spaceBefore=4)

story += [
    Paragraph("Why each method beats the previous (and when)", H1),
    Paragraph(
        "One short paragraph per method: the design pressure, what it fixed, "
        "and what is still wrong.",
        BODY),
    hr(),

    Paragraph("UER &rarr; PER", TIGHT_H),
    Paragraph(
        "<b>Why:</b> uniform sampling wastes compute on transitions the agent "
        "already understands. <b>Fix:</b> PER concentrates sampling on high "
        "TD-error transitions. <b>Still wrong:</b> in sparse-reward tasks, "
        "TD-error is ~0 almost everywhere, so PER degrades back toward uniform.",
        TIGHT),

    Paragraph("PER &rarr; HER", TIGHT_H),
    Paragraph(
        "<b>Why:</b> PER cannot extract signal from rewards that are never "
        "observed. <b>Fix:</b> HER manufactures successful transitions by "
        "relabeling the goal of failed episodes &mdash; every failure becomes a "
        "success at <i>some</i> goal. <b>Still wrong:</b> HER picks a goal but "
        "not a timestep, and assumes the env exposes achieved_goal.",
        TIGHT),

    Paragraph("HER &rarr; Semantic PER", TIGHT_H),
    Paragraph(
        "<b>Why:</b> in long-horizon manipulation, one or two transitions out "
        "of 50 typically cause the failure (grasp slipped, gripper missed by 2 cm). "
        "<b>Fix:</b> a VLM identifies where the failure happened; we boost those "
        "transitions on top of PER. <b>Still wrong:</b> VLMs are noisy &mdash; our "
        "36-run ablation shows GPT-4o under-performs a privileged-state heuristic.",
        TIGHT),

    Paragraph("Semantic PER &rarr; CF-HER", TIGHT_H),
    Paragraph(
        "<b>Why:</b> Semantic PER reweights existing transitions but does not "
        "change <i>what they say</i>. They still carry the failed reward. "
        "<b>Fix:</b> CF-HER asks the VLM to imagine an alternate goal G* and "
        "relabels accordingly. <b>Still wrong:</b> nothing forces G* to have "
        "been reached. On Push the VLM frequently proposes G* = desired_goal "
        "(teleport); reward stays 0.",
        TIGHT),

    Paragraph("CF-HER &rarr; Verified-CF", TIGHT_H),
    Paragraph(
        "<b>Why:</b> a synthetic transition that lies about its reward poisons "
        "the value function. <b>Fix:</b> Verified-CF executes the VLM's proposal "
        "in a forked simulator and accepts only if the env reward fires. "
        "<b>Still wrong:</b> needs a forkable sim. The VLM still must produce a "
        "coherent action sequence; if not, fall back to plain HER.",
        TIGHT),

    Spacer(1, 0.06 * inch),
    hr(),
    Paragraph("Empirical findings from our project (Fetch, 250k&ndash;1M steps)", H2),
    bullet(
        "<b>Path A:</b> Semantic PER with heuristic Oracle beats vanilla PER "
        "(<b>0.417 vs 0.383</b>, mean over 3 seeds, 1M steps).",
        GREEN),
    bullet(
        "<b>Path A (GPT-4o):</b> swap the Oracle for a VLM and it drops below "
        "PER (<b>0.31 vs 0.38</b>). Mechanism works; the VLM is the bottleneck.",
        ORANGE),
    bullet(
        "<b>Path C v1 (CF-HER):</b> does not beat plain HER on Fetch at the "
        "250k-step horizon. Teleport-collapse on Push dominates.",
        RED),
    bullet(
        "<b>Path C v2 (Verified-CF):</b> 4/4 smoke pass on sim-grounded "
        "verification; full training run launching today.",
        ACCENT),

    Spacer(1, 0.04 * inch),
    Paragraph(
        "<b>Headline lesson:</b> adding a VLM is not automatic. It helps when "
        "the VLM has a clear job, is calibrated against ground truth, and its "
        "outputs are structurally constrained (window weights, not arbitrary "
        "coordinates). It hurts when you ask it to invent physical-world facts "
        "without verifying them. Verified-CF is the principled response.",
        TIGHT),
]

doc.build(story)
print(f"wrote {OUT}")
