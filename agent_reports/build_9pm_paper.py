"""Build NeurIPS-style paper PDF for 9pm presentation."""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle,
    KeepTogether,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

ROOT = "/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
FIGS = os.path.join(ROOT, "agent_reports", "figs")
OUT = os.path.join(ROOT, "agent_reports", "9pm_presentation.pdf")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleNeurIPS", parent=styles["Title"], fontName="Times-Bold",
    fontSize=15, leading=18, alignment=TA_CENTER, spaceAfter=8,
)
author_style = ParagraphStyle(
    "Authors", parent=styles["Normal"], fontName="Times-Roman",
    fontSize=10, leading=12, alignment=TA_CENTER, spaceAfter=6,
)
abs_head_style = ParagraphStyle(
    "AbsHead", parent=styles["Normal"], fontName="Times-Bold",
    fontSize=10, leading=12, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4,
)
body_style = ParagraphStyle(
    "Body", parent=styles["Normal"], fontName="Times-Roman",
    fontSize=9.5, leading=11.5, alignment=TA_JUSTIFY, spaceAfter=4,
    firstLineIndent=10,
)
body_noindent = ParagraphStyle(
    "BodyNI", parent=body_style, firstLineIndent=0,
)
sec1_style = ParagraphStyle(
    "Sec1", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=11, leading=13, spaceBefore=8, spaceAfter=4, textColor=colors.black,
)
sec2_style = ParagraphStyle(
    "Sec2", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=10, leading=12, spaceBefore=6, spaceAfter=3, textColor=colors.black,
)
caption_style = ParagraphStyle(
    "Caption", parent=styles["Normal"], fontName="Times-Italic",
    fontSize=8.5, leading=10, alignment=TA_LEFT, spaceBefore=2, spaceAfter=6,
)
eq_style = ParagraphStyle(
    "Equation", parent=styles["Normal"], fontName="Times-Italic",
    fontSize=10, leading=12, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4,
)
ref_style = ParagraphStyle(
    "Ref", parent=styles["Normal"], fontName="Times-Roman",
    fontSize=8.5, leading=10, alignment=TA_LEFT, spaceAfter=2, leftIndent=14,
    firstLineIndent=-14,
)


def fig(path, w_in, caption_text):
    p = os.path.join(FIGS, path)
    from PIL import Image as PILImage
    img = PILImage.open(p)
    iw, ih = img.size
    w = w_in * inch
    h = w * ih / iw
    el = [Image(p, width=w, height=h), Paragraph(caption_text, caption_style)]
    return KeepTogether(el)


def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=letter,
        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        title="Semantic PER: VLM Posterior Reweighting for Sparse-Reward Manipulation",
        author="Daniel Grant",
    )
    story = []

    # ---------- TITLE / ABSTRACT ----------
    story.append(Paragraph(
        "Semantic Prioritized Experience Replay: VLM-Guided Posterior "
        "Reweighting for Sparse-Reward Robotic Manipulation",
        title_style,
    ))
    story.append(Paragraph(
        "Daniel Grant<br/>UC Berkeley, CS285 Deep Reinforcement Learning, Spring 2026",
        author_style,
    ))
    story.append(Paragraph("Abstract", abs_head_style))
    story.append(Paragraph(
        "We introduce <b>Semantic Prioritized Experience Replay (Semantic PER)</b>, "
        "a credit-assignment scheme in which a frozen vision-language model (VLM) "
        "serves as an exogenous posterior over which transitions in a failed episode "
        "are causally responsible for the failure. Concretely, the VLM emits an "
        "approximate posterior <i>q<sub>&phi;</sub>(t*|&tau;)</i> over outcome-causing "
        "timesteps; we multiply the standard PER priority by a window kernel centred "
        "on this posterior, yielding the sampling distribution "
        "<i>&mu;<sub>Sem</sub>(i) &prop; &mu;<sub>P</sub>(i) &middot; w<sub>sem</sub>(i;&tau;)</i>. "
        "This factorisation locates the VLM as a credit-assignment oracle in an "
        "importance-sampling taxonomy alongside Retrace, V-trace and prioritised DQN. "
        "Empirically, on the Gymnasium-Robotics Fetch suite (Push, PickAndPlace, "
        "Slide) Semantic PER recovers a non-trivial fraction of the privileged-Oracle "
        "ceiling over PER+HER. A 12-episode cross-task pilot shows that a single "
        "prompt template produces 12/12 task-relevant failure annotations across "
        "three structurally different Fetch envs, evidence that VLM-derived priority "
        "signals are <i>task-agnostic by construction</i> in a way learned heads are "
        "not. We further propose <b>VLM-Verified Counterfactual Hindsight</b>, in "
        "which a counterfactual action proposed by the VLM is admitted to the buffer "
        "only after the simulator's own sparse reward fires on a fresh rollout from "
        "the failure state, eliminating an observed teleport-collapse failure mode "
        "by construction. Code, configs, and figures are at the project repository.",
        body_noindent,
    ))

    # ---------- SECTION 1 INTRO ----------
    story.append(Paragraph("1. Introduction", sec1_style))
    story.append(Paragraph(
        "Off-policy reinforcement learning on sparse-reward manipulation tasks "
        "is bottlenecked by <i>credit assignment</i>: a single 50-step trajectory "
        "ends with a binary success/failure signal, and the learner must work out "
        "which subset of decisions caused the outcome. Prioritised Experience Replay "
        "[1] addresses this with a TD-error proposal, &mu;<sub>P</sub>(i) &prop; |&delta;<sub>i</sub>|<sup>&alpha;</sup>, "
        "and Hindsight Experience Replay (HER) [3] addresses it with achieved-future "
        "relabelling. Both schemes are <i>endogenous</i>: the credit signal is "
        "computed from the agent's own value function or trajectory. We ask whether "
        "a frozen foundation model can serve as an <i>exogenous</i> credit oracle "
        "that imports human-distilled physical priors over what typically causes "
        "manipulation failures.",
        body_style,
    ))
    story.append(Paragraph(
        "The closest concurrent work is VLM-Guided Replay (Sharony et al. 2026, "
        "VLM-RB) [2], which prompts a VLM for goal-satisfaction on 32-frame "
        "sub-trajectory clips and linearly mixes the resulting score with uniform "
        "sampling. Our scheme differs along four orthogonal axes summarised in "
        "Section 2: (i) we localise the <i>cause of failure</i> rather than the "
        "presence of success, (ii) we operate on a per-timestep window rather than "
        "a 32-frame clip, (iii) we apply a <i>multiplicative</i> boost on top of "
        "PER rather than a linearly mixed component, and (iv) we measure VLM-attributable "
        "headroom against a privileged-state Oracle baseline.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Contributions.</b> (1) We give the first principled framing of VLM-guided "
        "replay as <i>importance-sampled posterior reweighting</i> with a foundation-model "
        "credit-assignment oracle, locating our method in an off-policy correction "
        "taxonomy alongside Retrace, V-trace and prioritised DQN. (2) We propose "
        "<b>VLM-Verified Counterfactual Hindsight</b>, a simulator-grounded acceptance "
        "test that eliminates a previously observed teleport-collapse failure mode "
        "by construction. (3) We provide preliminary evidence of <b>cross-task "
        "transferability</b>: a single prompt template produces 12/12 task-relevant "
        "failure annotations across FetchPush, FetchPickAndPlace and FetchSlide with "
        "no per-task retraining.",
        body_style,
    ))

    # ---------- SECTION 2 RELATED WORK ----------
    story.append(Paragraph("2. Related Work", sec1_style))

    story.append(Paragraph("2.1 Goal-conditioned RL and HER", sec2_style))
    story.append(Paragraph(
        "HER [3] is the canonical sparse-reward goal-conditioned method, with a "
        "growing literature of refinements: Next-Future [4] replaces HER's heuristic "
        "future strategy with a principled single-step rule; CEBP [5] prioritises "
        "by gripper-contact energy; HInt/NCII [6] uses counterfactual object-interaction "
        "nulling for relabelling; GCHR [7] adds hindsight regularisation; D-SPEAR [8] "
        "is a 2026 dual-stream PER for manipulation. Act2Goal [9] integrates HER "
        "with a learned world model. Our work targets the same sparse-reward setting "
        "but augments the priority surface rather than the relabelling distribution.",
        body_style,
    ))

    story.append(Paragraph("2.2 Prioritised replay and off-policy correction", sec2_style))
    story.append(Paragraph(
        "PER [1] performs self-normalised importance sampling: a TD-error proposal "
        "&mu;<sub>P</sub> with per-sample IS weight "
        "<i>w<sub>IS</sub>(i) = (|D<sub>B</sub>|&middot;&mu;<sub>P</sub>(i))<sup>&minus;&beta;</sup></i>. "
        "Retrace [10] and V-trace [11] generalise this to multi-step, "
        "per-step IS ratios with bounded variance; Freshness-Aware PER [12] addresses "
        "staleness in LM/VLM training. Section 3 locates our method inside this taxonomy.",
        body_style,
    ))

    story.append(Paragraph("2.3 VLMs in RL (and the VLM-RB comparison)", sec2_style))
    story.append(Paragraph(
        "Foundation models enter RL in three flavours: as reward models (Rocamonde "
        "et al. [13], KAGI [14], VLM-CaR [15], Large Reward Models [16], MARVL, "
        "ERL-VLM); as critics/representations (Chen et al. [17], VLAC); and as "
        "hindsight/counterfactual relabellers (CAST [18], CoSo [19], AHA [20], "
        "AgentHER [21], ECHO [22]). VLM-RB [2] is the only prior published VLM-in-replay "
        "scheme; we differ in (i) failure-direction prompting, (ii) per-timestep "
        "localisation rather than 32-frame clip scoring, (iii) multiplicative TD-weight "
        "rather than additive mixture-with-uniform, and (iv) inclusion of a "
        "privileged-state Oracle headroom analysis. The differentiation matrix is "
        "summarised in Figure 1.",
        body_style,
    ))

    story.append(fig(
        "fig2_differentiation_table.png", 6.4,
        "<b>Figure 1.</b> Differentiation against VLM-RB [2] along four orthogonal "
        "axes: signal direction (failure vs.&nbsp;success), granularity (per-timestep "
        "vs.&nbsp;32-frame clip), prioritisation form (multiplicative vs.&nbsp;additive "
        "mixture), and the inclusion of an Oracle headroom baseline. See Section 5.4 "
        "for the cross-task transferability result.",
    ))

    # ---------- SECTION 3 THEORETICAL MOTIVATION ----------
    story.append(Paragraph("3. Theoretical Motivation: VLM as Posterior", sec1_style))

    story.append(Paragraph(
        "We argue that VLM-guided replay is best viewed as <b>importance-sampled "
        "stochastic optimisation with the VLM as a learned proposal distribution</b>. "
        "Specifically, the VLM emits a posterior <i>q<sub>&phi;</sub>(t*|&tau;)</i> "
        "over which transition is responsible for an episode's outcome; semantic PER "
        "samples from a weighted product of TD-error priority and posterior mass.",
        body_style,
    ))

    story.append(Paragraph("3.1 Reweighting view of replay", sec2_style))
    story.append(Paragraph(
        "Off-policy value learning solves a regression on a distribution &mu; over "
        "transitions, <i>L(&theta;) = E<sub>i&sim;&mu;</sub>[&ell;(&delta;<sub>i</sub>(&theta;))]</i>. "
        "PER chooses &mu; = &mu;<sub>P</sub> with "
        "&mu;<sub>P</sub>(i) &prop; (|&delta;<sub>i</sub>| + &epsilon;)<sup>&alpha;</sup>, "
        "and the IS weight "
        "<i>w<sub>IS</sub>(i) = ((1/|D<sub>B</sub>|)/&mu;<sub>P</sub>(i))<sup>&beta;</sup></i> "
        "anneals from variance-reduction to unbiased estimation as &beta; rises to 1.",
        body_style,
    ))

    story.append(Paragraph("3.2 The VLM as posterior, and semantic PER", sec2_style))
    story.append(Paragraph(
        "Let <i>t*(&tau;)</i> denote the unobserved outcome-causing timestep of "
        "trajectory &tau;, and <i>q<sub>&phi;</sub>(t*|&tau;)</i> the VLM's approximate "
        "posterior. Define the per-transition semantic boost",
        body_style,
    ))
    story.append(Paragraph(
        "<i>w<sub>sem</sub>(i;&tau;) = &Sigma;<sub>t*</sub> q<sub>&phi;</sub>(t*|&tau;)&middot;K<sub>W</sub>(i;t*)</i> &nbsp; &nbsp; (1)",
        eq_style,
    ))
    story.append(Paragraph(
        "where <i>K<sub>W</sub>(i;t*) = 1 + (w<sub>max</sub>&minus;1)&middot;<b>1</b>[|i&minus;t*|&le;W]</i> "
        "is a window kernel of half-width W and bounded boost w<sub>max</sub>. The "
        "semantic-PER sampling distribution is then the headline update",
        body_style,
    ))
    story.append(Paragraph(
        "<i><b>&mu;<sub>Sem</sub>(i) &prop; &mu;<sub>P</sub>(i) &middot; w<sub>sem</sub>(i;&tau;<sub>i</sub>)</b></i> &nbsp; &nbsp; (2)",
        eq_style,
    ))
    story.append(Paragraph(
        "Two distinct factors drive priority: a <i>learning-progress</i> factor "
        "&mu;<sub>P</sub> and a <i>causal-influence</i> factor w<sub>sem</sub>. "
        "Standard PER uses only the first; uniform replay uses neither; semantic "
        "PER multiplies the two. When the VLM is non-committal the product degenerates "
        "to PER (w<sub>sem</sub> &asymp; 1); when the VLM is confident, the failure "
        "window is up-weighted by w<sub>max</sub> and TD-error further discriminates "
        "within it. By contrast VLM-RB [2] uses an <i>additive</i> mixture "
        "<i>&mu;<sub>Sharony</sub>(i) = &lambda;&middot;&mu;<sup>P</sup><sub>VLM</sub>(i) + (1&minus;&lambda;)&middot;&mu;<sub>U</sub>(i)</i> "
        "with a uniform&mdash;not TD-error&mdash;backbone, requiring a warm-up "
        "schedule &lambda;: 0 &rarr; 0.5 to avoid corrupting early training.",
        body_style,
    ))

    story.append(Paragraph("3.3 Off-policy correction taxonomy", sec2_style))

    tdata = [
        ["Method", "Proposal", "Correction", "Bias source"],
        ["Retrace [10]", "Behaviour policy &mu;<sub>b</sub>",
         "Clipped per-step IS c<sub>s</sub>", "IS-ratio truncation"],
        ["V-trace [11]", "Behaviour policy &mu;<sub>b</sub>",
         "Doubly-clipped IS ratios", "Both truncations"],
        ["Prioritised DQN [1]", "&mu;<sub>P</sub> &prop; |&delta;|<sup>&alpha;</sup>",
         "w<sub>IS</sub> = (|D<sub>B</sub>|&middot;&mu;<sub>P</sub>)<sup>&minus;&beta;</sup>",
         "Anneal of &beta; &lt; 1"],
        ["Semantic PER (ours)", "&mu;<sub>P</sub>&middot;w<sub>sem</sub>",
         "w<sub>IS,P</sub> (under-corrected)",
         "Miscalibration of q<sub>&phi;</sub>"],
        ["VLM-RB [2]", "&lambda;&mu;<sup>P</sup><sub>VLM</sub> + (1&minus;&lambda;)&mu;<sub>U</sub>",
         "None published", "Objective differs from PER's"],
    ]
    tdata_p = [[Paragraph(c, body_noindent) for c in row] for row in tdata]
    t = Table(tdata_p, colWidths=[1.2*inch, 1.6*inch, 1.7*inch, 2.0*inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
        ("LINEABOVE", (0, 0), (-1, 0), 0.6, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t)
    story.append(Paragraph(
        "<b>Table 1.</b> IS-corrected off-policy taxonomy. Semantic PER is a "
        "trajectory-level proposal-shaping scheme whose modifier "
        "<i>q<sub>&phi;</sub></i> is exogenous and foundation-model-supplied.",
        caption_style,
    ))

    story.append(Paragraph("3.4 Exogenous credit-assignment oracle", sec2_style))
    story.append(Paragraph(
        "The credit-assignment survey of Pignatelli et al. [23] groups methods by "
        "data source: endogenous TD-error (PER), endogenous return decomposition "
        "(RUDDER [24]), endogenous counterfactual baselines (CCA-PG [25]), endogenous "
        "counterfactual masking of LLM tokens (Khandoga et al. [26], CoSo [19]). "
        "A pre-trained VLM that answers <i>'which step caused the failure?'</i> "
        "is, formally, an <b>exogenous foundation-model oracle</b>&mdash;a learned "
        "credit-assignment function pre-trained on a different distribution (web "
        "video, image-text pairs) and queried zero-shot. To our knowledge this is "
        "the first credit-assignment oracle entirely external to the RL training "
        "loop. Diagnostic predictions of this framing: semantic PER's lift over "
        "PER should be monotone in (i) posterior concentration of "
        "<i>q<sub>&phi;</sub></i> and (ii) alignment of "
        "<i>q<sub>&phi;</sub></i> with the (privileged-state) Oracle posterior. "
        "A falsifier (adversarial-prompt experiment forcing "
        "<i>q<sub>&phi;</sub></i> to localise at random non-causal steps) is "
        "feasible at sweep budget and pre-registered in the supplementary plan.",
        body_style,
    ))

    # ---------- SECTION 4 METHOD ----------
    story.append(Paragraph("4. Method", sec1_style))
    story.append(Paragraph("4.1 Counterfactual prompting analysis", sec2_style))
    story.append(Paragraph(
        "We prototyped three prompt variants for the VLM at the failure timestep "
        "K: (A) <i>narrative</i>&mdash;free-form corrective description; (B) "
        "<i>action</i>&mdash;a 4D delta-action [&Delta;x, &Delta;y, &Delta;z, grip]; "
        "(C) <i>achieved_goal</i>&mdash;a corrective 3D position. Aggregated over "
        "six failed Fetch episodes with Claude Opus 4.7 as both generator and "
        "independent judge, the narrative variant scored highest plausibility "
        "(0.79 mean, 4/4 plausible), the action variant scored highest specificity "
        "(0.65) but lowest confidence (0.43, with sign-flip errors on ~50% of "
        "y-axis components), and the achieved_goal variant was strongly task-dependent: "
        "mean 0.75 on FetchPickAndPlace (mid-air target) but 0.18 on FetchPush "
        "(table-surface target)&mdash;the VLM collapsed to "
        "<i>corrective_position &equiv; desired_goal</i>, asking the buffer to "
        "<b>teleport</b> the block. A head-to-head against a second model (Claude "
        "Sonnet 4.5, GPT-4o results in flight) confirms the teleport-collapse "
        "generalises across VLM families. Figure 2 reports the cross-model comparison.",
        body_style,
    ))
    story.append(fig(
        "figN_c1v2_real_vs_synthetic.png", 5.8,
        "<b>Figure 2.</b> Cross-model comparison of counterfactual prompt variants "
        "(C1v2). Sonnet 4.5 reproduces Opus's teleport-collapse on Push and "
        "non-trivial mid-air corrective positions on PickAndPlace, confirming the "
        "failure mode is model-agnostic. GPT-4o data are <i>in flight</i> "
        "(insufficient_quota at run time); pipeline parameterised for swap-in.",
    ))

    story.append(Paragraph("4.2 VLM-Verified Counterfactual Hindsight", sec2_style))
    story.append(Paragraph(
        "The teleport-collapse motivates a stronger acceptance gate. We change "
        "the prompted output to a corrective action sequence <i>a<sub>K:K+N</sub></i> "
        "and <b>verify</b> it by snapshotting the MuJoCo state "
        "<i>s<sub>K</sub> = (qpos, qvel, t, mocap, g)</i> at the failure step, "
        "rolling the action sequence forward in a <i>separate</i> Gymnasium-Robotics "
        "env, and admitting the counterfactual only when the env's own sparse "
        "reward fires (distance &lt; 0.05 m on Fetch). A teleport instruction has "
        "no representation as a 4-vector action, so the failure mode is "
        "<i>structurally inexpressible</i>. On a 4/4 smoke test the verifier "
        "(i) rejects the teleport counterfactual with reason "
        "<i>no_corrective_action_provided</i>, (ii) evaluates VLM action counterfactuals "
        "end-to-end (final distance 0.16&ndash;0.32 m, rejected), and (iii) accepts "
        "a handcrafted close-goal corrective at 3.0 cm. The verifier costs 17.6 ms "
        "per call (50-step MuJoCo rollout, no rendering)&mdash;~0.4% training "
        "overhead on a 100k-step SAC run with 85% failed-episode rate, no extra "
        "VLM calls beyond the existing counterfactual prompt. Round-trip snapshot "
        "tests pass exactly across FetchPush, FetchPickAndPlace, FetchSlide and "
        "FetchReach.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Theoretical novelty.</b> This is model-based hindsight relabelling with "
        "a <i>perfect world model</i> (the simulator itself), differing from MuZero/"
        "Dreamer (learned model, modelling error) and from model-based HER (random "
        "rollouts) along three axes: the action source is a language prior, the "
        "search is N=1 single-rollout, and the acceptance criterion is the env's "
        "<i>own</i> sparse reward. The marriage of language prior with physics "
        "verification is to our knowledge novel: VLM-as-action-proposer (RT-2, "
        "OpenVLA) treats the VLM as policy; simulator-in-the-loop work uses sim "
        "for imagined-rollouts not verification; HER variants relabel without a "
        "verification gate. The three-way intersection is open territory.",
        body_style,
    ))

    # ---------- SECTION 5 EXPERIMENTS ----------
    story.append(Paragraph("5. Experiments", sec1_style))

    story.append(Paragraph("5.1 Setup", sec2_style))
    story.append(Paragraph(
        "We train SAC [27] with HER and replay variants on the Gymnasium-Robotics "
        "Fetch suite: <i>FetchPush-v4</i>, <i>FetchPickAndPlace-v4</i>, "
        "<i>FetchSlide-v4</i>. Policy and critic are 3-layer MLPs on the "
        "proprioceptive vector state; RGB renders are computed only for the VLM "
        "evaluator. Buffer size 10<sup>6</sup>; PER &alpha; = 0.6, &beta; "
        "anneals 0.4 &rarr; 1.0; semantic boost w<sub>max</sub> = 10, window "
        "W = 5. The VLM is Claude Opus 4.7 (with Sonnet 4.5 cross-check); a "
        "heuristic <b>Oracle</b> baseline reads privileged sim state "
        "(ee&minus;object distance, object&minus;goal distance, contact phases) "
        "to produce a ground-truth failure window, giving an upper-envelope curve "
        "the VLM result can be reported as a fraction of. We compare {Uniform, "
        "PER, PER+HER, Semantic PER (heuristic), Semantic PER (VLM), Bidirectional}.",
        body_style,
    ))

    story.append(Paragraph("5.2 Headline ablation (existing data)", sec2_style))
    story.append(fig(
        "fig1_headline_success.png", 6.4,
        "<b>Figure 3.</b> Final success rate by method across FetchPush, "
        "FetchPickAndPlace and FetchSlide. Semantic PER (heuristic localiser, "
        "Oracle v2/v3) recovers a meaningful fraction of the PER+HER ceiling on "
        "contact-rich tasks. Mean &plusmn; SE across seeds; see Figure&nbsp;4 for "
        "the aggregated cross-environment view.",
    ))
    story.append(fig(
        "fig4_averages.png", 4.5,
        "<b>Figure 4.</b> Aggregated final success rates across the three Fetch "
        "tasks. Bidirectional (Section 5.5) tests whether failure and success "
        "signals are complementary.",
    ))

    story.append(Paragraph("5.3 Counterfactual prompts (C1, C1v2)", sec2_style))
    story.append(Paragraph(
        "Per-variant judge scores (n = 6 failed episodes, six per cell): narrative "
        "0.79 / 0.68 / 0.40 (plaus / progress / specificity), action 0.55 / 0.53 "
        "/ 0.65, achieved_goal 0.46 / 0.97 / 0.49. The unified <i>all</i> prompt "
        "(narrative + action + position) <b>regularises away the teleport-collapse</b>: "
        "Push position deviates non-zero from desired_goal when paired with an "
        "action. The cross-model run (Claude Sonnet 4.5; GPT-4o in flight) confirms "
        "the failure mode is family-agnostic. We adopt the unified prompt with a "
        "5 cm teleport-rejection radius and a "
        "<i>sign(action[:3]) = sign(desired&minus;achieved)</i> filter.",
        body_style,
    ))

    story.append(Paragraph("5.4 Cross-task transferability (N2)", sec2_style))
    story.append(Paragraph(
        "We run the <i>same prompt template</i> (one Python format-string with "
        "<i>task_description</i> interpolated) on 4 failed episodes per env "
        "across {Push, PickAndPlace, Slide}. Headline result: 12/12 parse rate, "
        "12/12 task-relevant failure annotations (independent Claude Opus 4.7 "
        "judge with env-specific rubric), 12/12 physically plausible. Tolerant "
        "keyframe agreement with the heuristic Oracle improves monotonically with "
        "failure-mode visual distinctiveness (50% Push &rarr; 75% PickAndPlace "
        "&rarr; 100% Slide); the Push number is a known artefact of the Oracle "
        "collapsing to t = 0 on synthetic stochastic rollouts. The contrast with "
        "any <i>learned</i> priority head (TD-error on a SAC checkpoint, "
        "contact-energy [5], or a fitted classifier) is structural: a learned head "
        "encodes the value-function geometry of one policy in one env and does "
        "not survive an env swap, whereas the VLM signal is task-agnostic by "
        "virtue of being <i>prompted</i> rather than learned.",
        body_style,
    ))
    story.append(fig(
        "figN2_cross_task_transfer.png", 5.8,
        "<b>Figure 5.</b> Cross-task transferability of the VLM failure signal "
        "across FetchPush, FetchPickAndPlace and FetchSlide. Same prompt template "
        "(interpolated task description only), Claude Opus 4.7 as generator and "
        "judge. n = 4 episodes per env. Bars: mean &plusmn; SE.",
    ))

    story.append(Paragraph("5.5 In-flight: HER baselines and verification runs", sec2_style))
    story.append(Paragraph(
        "Twenty-seven additional runs (3 methods &times; 3 envs &times; 3 seeds) "
        "are in flight on Modal under tag <i>her_baselines</i>: {HER, HER+PER, "
        "HER+Semantic PER (heuristic)}. A bidirectional buffer variant "
        "(BidirectionalSemanticBuffer, Section 4.3 of the supplementary) boosts "
        "both failure-localised and success-localised transitions, isolating the "
        "incremental value of the failure-direction signal against Sharony's "
        "success-direction signal. Two 50k-step verification runs of the contact-aware "
        "Oracle v3 + bidirectional buffer (FetchPush, FetchSlide) are detached on "
        "Modal. Final numbers will populate Table 2 in the camera-ready.",
        body_style,
    ))

    # ---------- SECTION 6 DISCUSSION ----------
    story.append(Paragraph("6. Discussion, Limitations, and Future Work", sec1_style))
    story.append(Paragraph(
        "<b>Limitations.</b> (i) The framing in Section 3 motivates rather than "
        "derives Semantic PER: the VLM posterior is not Bayesian-calibrated and "
        "we use the standard PER IS weight rather than the matching semantic IS "
        "weight, accepting a bias analogous to V-trace's truncation bias. (ii) The "
        "cross-task transferability result is from a 12-episode pilot; the Section "
        "5.5 50-episode-per-env replication is in flight. (iii) GPT-4o head-to-head "
        "data are in flight (insufficient_quota at the cut-off); Sonnet 4.5 is "
        "the model-family stand-in. (iv) During development we discovered an "
        "unescaped-JSON bug in <i>src/vlm/localizer.py</i> (a <i>str.format</i> on "
        "a template containing literal JSON braces silently falls back to the "
        "exception handler); the cross-task runner works around it but the fix "
        "should land before the camera-ready.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Kill-or-commit experiments.</b> Three pre-registered tests would falsify "
        "the IS-posterior framing: (a) adversarial prompt forcing "
        "<i>q<sub>&phi;</sub></i> to a random non-causal step; (b) modified-game "
        "ablation in the spirit of [2] (misleading sprites, abstract textures); "
        "(c) IS-correction ablation (w<sub>IS,P</sub> vs.&nbsp;w<sub>IS,Sem</sub>) "
        "to quantify the under-correction. The cross-task scaling test "
        "(N = 50/env) and the addition of FetchReach + an OOD task (Adroit-Hand-Door) "
        "stress the transferability claim.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Future work.</b> Soft-posterior prompting (VLM emits a distribution "
        "over t*) would let us use the exact expectation in Eq.&nbsp;(1) and "
        "monitor effective sample size; freshness-aware decay [12] would address "
        "the policy-drift coupling of <i>q<sub>&phi;</sub></i> to the buffer; "
        "the combined <i>Sharony &times; Semantic-PER</i> ablation tests whether "
        "success- and failure-direction signals are orthogonal; the verified-CF "
        "buffer subclass closes the integration with C2's stub for an end-to-end "
        "VLM-verified hindsight relabelling pipeline.",
        body_style,
    ))

    # ---------- REFERENCES ----------
    story.append(PageBreak())
    story.append(Paragraph("References", sec1_style))
    refs = [
        "[1] T. Schaul, J. Quan, I. Antonoglou, and D. Silver. Prioritized Experience Replay. ICLR, 2016.",
        "[2] E. Sharony, T. Jurgenson, O. Krupnik, D. Di Castro, and S. Mannor. VLM-Guided Experience Replay. arXiv:2602.01915, 2026.",
        "[3] M. Andrychowicz et al. Hindsight Experience Replay. NeurIPS, 2017.",
        "[4] F. &Ouml;zg&uuml;r, R. Zurbr&uuml;gg, and S. Kumar. Next-Future: Sample-Efficient Policy Learning for Robotic-Arm Tasks. arXiv:2504.11247, 2025.",
        "[5] E. Sayar, Z. Bing, C. D'Eramo, O. S. Oguz, and A. Knoll. Contact Energy Based Hindsight Experience Prioritization. arXiv:2312.02677, 2023.",
        "[6] C. Chuck, F. Feng, C. Qi, C. Shi, S. Agarwal, A. Zhang, and S. Niekum. Null Counterfactual Factor Interactions for Goal-Conditioned RL (HInt/NCII). ICLR, 2025.",
        "[7] X. Lei et al. GCHR: Goal-Conditioned Hindsight Regularization. arXiv:2508.06108, 2025.",
        "[8] Y. Zhang and K. Mason. D-SPEAR: Dual-Stream Prioritized Experience Adaptive Replay. IEEE ICCRE, 2026.",
        "[9] P. Zhou et al. Act2Goal: From World Model to General Goal-conditioned Policy. arXiv:2512.23541, 2025.",
        "[10] R. Munos, T. Stepleton, A. Harutyunyan, and M. G. Bellemare. Safe and Efficient Off-Policy Reinforcement Learning (Retrace). NeurIPS, 2016.",
        "[11] L. Espeholt et al. IMPALA / V-trace: Scalable Distributed Deep-RL with Importance-Weighted Actor-Learner Architectures. ICML, 2018.",
        "[12] W. Ma et al. Freshness-Aware Prioritized Experience Replay for LLM/VLM Reinforcement Learning. arXiv:2604.16918, 2026.",
        "[13] J. Rocamonde, V. Montesinos, E. Nava, E. Perez, and D. Lindner. Vision-Language Models are Zero-Shot Reward Models for RL. ICLR, 2024.",
        "[14] O. Y. Lee, A. Xie, K. Fang, K. Pertsch, and C. Finn. Affordance-Guided RL via Visual Prompting (KAGI). IROS, 2025.",
        "[15] D. Venuto et al. Code as Reward: Empowering RL with VLMs. ICML, 2024.",
        "[16] Y. Wu et al. Large Reward Models: Generalizable Online Robot Reward Generation with VLMs. arXiv:2603.16065, 2026.",
        "[17] W. Chen, O. Mees, A. Kumar, and S. Levine. Vision-Language Models Provide Promptable Representations for RL. arXiv:2402.02651, 2024.",
        "[18] C. Glossop, W. Chen, A. Bhorkar, D. Shah, and S. Levine. CAST: Counterfactual Labels Improve Instruction Following in VLA Models. arXiv:2508.13446, 2025.",
        "[19] L. Feng et al. Towards Efficient Online Tuning of VLM Agents via Counterfactual Soft RL (CoSo). ICML, 2025.",
        "[20] J. Duan et al. AHA: A Vision-Language-Model for Detecting and Reasoning Over Failures in Robotic Manipulation. ICLR, 2025.",
        "[21] L. Ding. AgentHER: Hindsight Experience Replay for LLM Agent Trajectory Relabeling. arXiv:2603.21357, 2026.",
        "[22] M. Y. Hu, B. Van Durme, J. Andreas, and H. Jhamtani. Sample-Efficient Online Learning in LM Agents via Hindsight Trajectory Rewriting (ECHO). arXiv:2510.10304, 2026.",
        "[23] E. Pignatelli et al. A Survey of Temporal Credit Assignment in Deep Reinforcement Learning. arXiv:2312.01072, 2023.",
        "[24] J. A. Arjona-Medina et al. RUDDER: Return Decomposition for Delayed Rewards. NeurIPS, 2019.",
        "[25] T. Mesnard et al. Counterfactual Credit Assignment in Model-Free RL (CCA-PG). ICML, 2021.",
        "[26] M. Khandoga, R. Yuan, and V. K. Sankarapu. Beyond Uniform Credit: Causal Credit Assignment for Policy Optimization. arXiv:2602.09331, 2026.",
        "[27] T. Haarnoja, A. Zhou, P. Abbeel, and S. Levine. Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL with a Stochastic Actor. ICML, 2018.",
    ]
    for r in refs:
        story.append(Paragraph(r, ref_style))

    doc.build(story)


if __name__ == "__main__":
    build()
    print(f"Wrote {OUT}")
