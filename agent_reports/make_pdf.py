"""Assemble the 9pm presentation PDF from figures + agent reports."""
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
OUT = REPORTS / "9pm_presentation.pdf"

# --- detect which late-breaking agent reports landed ------------------
HAS_N3 = (REPORTS / "N3_bayesian_framing.md").exists()
HAS_N1 = (REPORTS / "N1_verifiable_counterfactuals.md").exists() and (REPORTS / "N1_smoke_results.json").exists()
HAS_N2_MD = (REPORTS / "N2_cross_task_transfer.md").exists()
HAS_N2_JSON = (REPORTS / "N2_cross_task_validation_outputs.json").exists()
HAS_N2_FIG = (FIGS / "figN2_cross_task_transfer.png").exists()
HAS_N2 = HAS_N2_MD or HAS_N2_JSON
HAS_C1V2_MODEL = (REPORTS / "C1v2_model_comparison.md").exists()
HAS_C1V2_REAL_MD = (REPORTS / "C1v2_real_data.md").exists()
HAS_C1V2_REAL_FIG = any(FIGS.glob("figC1v2_real*.png")) or any(FIGS.glob("figC1v2B*.png"))
HAS_C1V2_REAL = HAS_C1V2_REAL_MD or HAS_C1V2_REAL_FIG

# --- styles -----------------------------------------------------------
DARK   = HexColor("#1f2d3d")
ACCENT = HexColor("#2c5d7d")
GREEN  = HexColor("#3aa66e")
ORANGE = HexColor("#d99151")
GRAY   = HexColor("#566573")
LIGHT  = HexColor("#ecf2f6")

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
                     fontName="Helvetica", fontSize=10, leading=13.5,
                     textColor=HexColor("#22313f"), spaceAfter=4,
                     alignment=TA_LEFT)
BODY_J = ParagraphStyle("BodyJ", parent=BODY, alignment=TA_JUSTIFY)
TLDR = ParagraphStyle("Tldr", parent=BODY, fontSize=10.5, leading=14.5,
                     textColor=DARK, leftIndent=14, bulletIndent=2,
                     spaceAfter=3)
CAPTION = ParagraphStyle("Cap", parent=BODY, fontSize=8.5, leading=11,
                         textColor=GRAY, alignment=TA_CENTER, spaceAfter=2)
META = ParagraphStyle("Meta", parent=BODY, fontSize=9, leading=12,
                     textColor=GRAY, spaceAfter=2, alignment=TA_LEFT)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8.5, leading=11,
                       textColor=HexColor("#3a4a59"), spaceAfter=2)


def hr():
    return HRFlowable(width="100%", thickness=0.7, color=HexColor("#bfcad3"),
                      spaceBefore=2, spaceAfter=6)


def img(path, w=7.2, caption=None):
    p = FIGS / path
    # measure aspect ratio
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
        TLDR
    )


def small_bullet(text):
    return Paragraph(f"&bull;&nbsp; {text}", SMALL)


# --- document ---------------------------------------------------------
doc = SimpleDocTemplate(
    str(OUT), pagesize=LETTER,
    leftMargin=0.6*inch, rightMargin=0.6*inch,
    topMargin=0.55*inch, bottomMargin=0.55*inch,
    title="Semantic Failure-Localized PER -- Team Sync 2026-05-11",
    author="Daniel Grant",
)

story = []

# =====================================================================
# PAGE 1 -- Title + TL;DR + headline chart
# =====================================================================
story += [
    Paragraph("Semantic Failure-Localized PER", H1),
    Paragraph(
        "Team sync, 2026-05-11 21:00 PDT &nbsp;&middot;&nbsp; "
        "Daniel Grant &nbsp;&middot;&nbsp; CS 285 (UC Berkeley) &nbsp;&middot;&nbsp; "
        "with Parshawn Gerafian, Matei Gardea",
        META,
    ),
    hr(),

    Paragraph("TL;DR", H2),
    bullet(
        "<b>Existing 36-run ablation stands.</b> Heuristic <b>Oracle wins on average "
        "(0.42)</b>; PER carries FetchPush; <b>GPT-4o variant under-performs PER (0.31 vs 0.38)</b> "
        "&mdash; VLM localization is the bottleneck, not the mechanism.",
        ACCENT,
    ),
    bullet(
        "<b>Tonight Path A:</b> HER baselines launched (27 Modal jobs, heuristic localizer, "
        "first eval points landing), Oracle <b>v3 contact-aware</b> shipped, and a "
        "<b>BidirectionalSemanticBuffer</b> (success + failure boost) wired in.",
        GREEN,
    ),
    bullet(
        "<b>Tonight Path C:</b> Counterfactual VLM prompts prototyped on 4 failed episodes; "
        "<b>Counterfactual-HER relabeling</b> recommended over reward shaping; "
        "<b>no scoop found</b> for VLM-counterfactual-for-RL.",
        ORANGE,
    ),
]

# Optional inset bullets for late-breaking agents
if HAS_C1V2_MODEL:
    story.append(bullet(
        "<b>C1v2-A model comparison (just landed):</b> GPT-4o vs Claude head-to-head &mdash; "
        "OpenAI API quota-blocked, so <b>Claude Sonnet 4.5</b> substituted as stand-in. "
        "Teleport-collapse on Push <i>persists across VLM families</i>; it is a prompt artefact, not a GPT-4o-specific bug. "
        "Sonnet 4.5 generally tracks Opus 4.7's variant ranking (judge narrative &gt; action &gt; achieved_goal).",
        GRAY,
    ))

if HAS_N1:
    story.append(bullet(
        "<b>N1 verifiable counterfactuals (just landed):</b> simulator-grounded acceptance test for VLM counterfactuals &mdash; "
        "<b>4/4 smoke pass, 17.6 ms overhead</b>, teleport rejected by construction.",
        DARK,
    ))

if HAS_N3:
    story.append(bullet(
        "<b>N3 theoretical framing (just landed):</b> Semantic PER recast as importance-sampled "
        "posterior reweighting &mdash; VLM is the proposal q&#x03C6;(t*|&tau;), our scheme is multiplicative on PER, "
        "Sharony's is additive mixture. Principled motivation for the paper.",
        ACCENT,
    ))

story += [
    Spacer(1, 0.08 * inch),
    hr(),

    img("fig1_headline_success.png", w=7.2,
        caption="Final eval success rate (mean over 3 seeds, error bars = SE). "
                "Source: existing 36-run ablation (1M steps each)."),

    Spacer(1, 0.04 * inch),
    img("fig4_averages.png", w=5.4,
        caption="Average across the three Fetch envs."),
]

story.append(PageBreak())

# =====================================================================
# PAGE 2 -- What was built tonight (Path A + Path C)
# =====================================================================
story += [
    Paragraph("What was built tonight", H1),
    Paragraph(
        "Five of six parallel agents have completed and committed code on isolated worktrees "
        "(branches <i>agent/a1-her-baselines</i>, <i>agent/a2-oracle-bidir</i>, "
        "<i>agent/c1-counterfactual-prompts</i>, <i>agent/c2-counterfactual-mechanism</i>, "
        "plus L1/L2 literature). The HER sweep is launched and live on W&amp;B; "
        "full numbers expected overnight.",
        BODY_J),
    hr(),

    img("fig3_paths_status.png", w=7.4,
        caption="Per-agent deliverables. All work committed to isolated branches; ready for review tomorrow."),

    Spacer(1, 0.06 * inch),
    Paragraph("Headline implementation details", H2),

    Paragraph("Path A &mdash; failure-direction prioritization", H3),
    small_bullet(
        "<b>Oracle v3 phase precedence:</b> ballistic &rarr; contact-loss &rarr; argmin. "
        "Contact loss fires when |ee &minus; obj| crosses 0.05 m with object still &gt; 0.10 m from goal &mdash; "
        "this is the moment a manipulation policy actually made a mistake on Push / PickAndPlace."
    ),
    small_bullet(
        "<b>BidirectionalSemanticBuffer:</b> per-slot success_weight and failure_weight; "
        "priority = (|delta| + eps)^alpha &times; w_failure &times; w_success. "
        "Slots inside both windows see 100&times; total boost; outside both, priority is identical to PER."
    ),
    small_bullet(
        "<b>HER sweep:</b> 27 jobs (her / her_per / her_semantic_per &times; 3 envs &times; 3 seeds), "
        "Modal app ap-RlxdhxgDoMSFobTyggIZG8, all tagged <i>her_baselines</i> on W&amp;B. "
        "First eval points landing; full results pending overnight."
    ),

    Spacer(1, 0.04 * inch),
    Paragraph("Path C &mdash; counterfactual VLM reasoning", H3),
    small_bullet(
        "<b>Prompts:</b> three variants tested on 4 failed Fetch rollouts using Claude Opus 4.7 as "
        "both generator and independent judge (OpenAI key not on this host; OpenAI codepath is wired). "
        "Mean judge plausibility: narrative <b>0.79</b> &middot; action <b>0.55</b> &middot; achieved_goal <b>0.46</b>."
    ),
    small_bullet(
        "<b>Key failure mode:</b> on planar tasks (Push) the achieved_goal variant collapses to "
        "<i>corrective_position == desired_goal</i> (teleport). Judge correctly rejects it. "
        "Mitigation: workspace-displacement filter, or use the unified prompt where the VLM stops "
        "short-circuiting."
    ),
    small_bullet(
        "<b>SAC integration:</b> Counterfactual-HER relabeling chosen over reward shaping and "
        "auxiliary-head exploration. Reasons: (a) <i>p_counterfactual = 0</i> recovers vanilla HER bit-for-bit, "
        "(b) bad VLM coords degrade gracefully (zero-reward synthetic transition, no value distortion), "
        "(c) orthogonal to Sharony's re-weighting axis."
    ),
    small_bullet(
        "<b>Decision gate:</b> Oracle-counterfactual upper-bound experiment is half a day of work and "
        "tells us whether the mechanism is strong enough to pursue. If oracle-CF does not beat HER by "
        "&ge;0.10 success on PickAndPlace, abandon Path C."
    ),
]

story.append(PageBreak())

# =====================================================================
# PAGE 3 -- Differentiation from Sharony 2602.01915
# =====================================================================
story += [
    Paragraph("Differentiation from Sharony et&nbsp;al. (arXiv 2602.01915)", H1),
    Paragraph(
        "<b>The scoop concern.</b> &quot;VLM-Guided Experience Replay&quot; "
        "(Sharony, Jurgenson, Krupnik, Di Castro, Mannor; Technion + NVIDIA; Feb&nbsp;2026) "
        "is concurrent work that uses a frozen VLM to score replay sub-trajectories. "
        "We were not aware of it when the project started. The four axes below establish that "
        "our contribution remains distinct on direction (failure vs success), granularity, blending, and "
        "headroom analysis &mdash; and that our empirical scope (Fetch) does not overlap theirs (MiniGrid + OGBench).",
        BODY_J),

    hr(),
    img("fig2_differentiation_table.png", w=7.4,
        caption="Side-by-side method comparison. Sources: arXiv:2602.01915 v1 (project page esharony.me/projects/vlm-rb); our agent reports."),

    Spacer(1, 0.04 * inch),
    Paragraph("Related-work paragraph (citation-ready)", H2),
    Paragraph(
        "Most closely related to our work is <b>VLM-RB (Sharony et&nbsp;al., 2026)</b>, "
        "which concurrently proposes using a frozen vision-language model to prioritize replay-buffer experiences. "
        "The two works differ along four orthogonal axes. "
        "First, VLM-RB up-weights transitions that the VLM judges to contain <b>goal-satisfaction</b>, "
        "whereas we up-weight transitions that the VLM identifies as the <b>cause of failure</b> &mdash; "
        "a sparser and arguably more credit-assignment-relevant signal in long-horizon sparse-reward control. "
        "Second, VLM-RB scores 32-frame sub-trajectory clips as atomic units; "
        "we localize a single failure timestep and apply a bounded window, yielding finer credit attribution. "
        "Third, VLM-RB linearly mixes a VLM-priority distribution with uniform sampling (requiring a lambda warm-up); "
        "we apply a <b>multiplicative weight to the PER priority</b>, which degrades gracefully to PER absent a VLM signal. "
        "Fourth, we introduce a <b>privileged-state Oracle</b> that decouples failure-prioritization-as-a-principle "
        "from VLM accuracy as an implementation, allowing us to report VLM-attributable headroom &mdash; "
        "an analysis absent in VLM-RB. "
        "We evaluate on Gymnasium-Robotics Fetch (Push, PickAndPlace, Slide) with SAC; "
        "VLM-RB evaluates on MiniGrid and OGBench Scene with DQN/IQN/SAC/TD3, so the empirical scopes are disjoint.",
        BODY_J),

    Spacer(1, 0.06 * inch),
    Paragraph("Path C extends the differentiation further", H2),
    small_bullet(
        "Sharony asks the VLM <i>which transitions matter</i>; "
        "Path C asks the VLM <i>what the goal should have been</i>."
    ),
    small_bullet(
        "Sharony re-weights existing transitions; "
        "Path C <i>generates synthetic transitions</i> from a VLM-imagined goal. "
        "These are orthogonal operations on the buffer &mdash; a combined "
        "<i>semantic_per &times; counterfactual_HER</i> variant is well-defined as future work."
    ),
    small_bullet(
        "Closest neighbours (L2 scoop check): CAST (counterfactual <i>language</i> labels for VLA imitation), "
        "CoSo (token-level masking in VLM agents), HInt/NCII (object-interaction counterfactuals with a learned dynamics model). "
        "<b>No published work</b> combines VLM counterfactual + PER + manipulation."
    ),
]

story.append(PageBreak())

# =====================================================================
# PAGE 4 -- Decisions needed + tomorrow's plan
# =====================================================================
story += [
    Paragraph("Decisions for the team &amp; tomorrow's plan", H1),
    hr(),

    Paragraph("Decisions we need to make tonight or first-thing tomorrow", H2),

    Paragraph("1.&nbsp; Do we commit to Path C, or stay all-in on Path A?", H3),
    Paragraph(
        "Path C (VLM counterfactuals as hindsight goals) is genuinely novel relative to Sharony, "
        "but it depends on GPT-4o producing 3D coordinates that are within ~5 cm of the actual target. "
        "C1's prototype shows the model has reasonable narrative reasoning but ~50% sign-flips on action vectors and "
        "task-dependent failure on the achieved_goal variant. <b>Recommendation:</b> run the cheap "
        "<i>oracle-counterfactual upper bound</i> first (half-day) to decide; if the oracle does not "
        "beat HER by &ge; 0.10 on PickAndPlace, abandon Path C and double down on Path A.",
        BODY_J),

    Paragraph("2.&nbsp; Is the failure-direction story strong enough to ship without Bidir &gt; Failure-only?", H3),
    Paragraph(
        "Our pitch is &quot;failure beats success.&quot; The headline experiment we still owe ourselves: "
        "<i>{Failure-only, Success-only, Bidirectional}</i> on the same 3 envs &times; 3 seeds. "
        "BidirectionalSemanticBuffer is implemented and Modal-verified. "
        "<b>Decision:</b> launch the head-to-head this week using the heuristic localizer to avoid API cost.",
        BODY_J),

    Paragraph("3.&nbsp; Do we re-launch the original 4-method ablation under our W&amp;B (d-grant-uc-berkeley)?", H3),
    Paragraph(
        "The 36 prior runs live under teammate's entity (djrgvc). Re-running uniform / PER / Semantic-PER-heuristic "
        "in our project is cheap (no API calls), gives clean filterable comparison, and produces a reproducible "
        "supplement for the paper. <b>Recommendation:</b> yes &mdash; tag everything under <i>her_baselines</i> and "
        "<i>direction_ablation</i>.",
        BODY_J),

    Spacer(1, 0.06 * inch),
    Paragraph("Tomorrow (Tue 5/12) &mdash; concrete plan", H2),
    small_bullet(
        "<b>Morning:</b> pull HER sweep results from W&amp;B (filter tag <i>her_baselines</i>); "
        "regenerate the headline plot with HER as a fifth method; check whether HER + Semantic PER stacks beat HER alone."
    ),
    small_bullet(
        "<b>Mid-day:</b> launch the direction-ablation sweep "
        "({failure_only, success_only, bidir} &times; 3 envs &times; 3 seeds, heuristic only). ~9 GPU-hours."
    ),
    small_bullet(
        "<b>Afternoon:</b> oracle-counterfactual upper-bound experiment on FetchPickAndPlace (Path C kill-test). "
        "If it passes, wire C1's CounterfactualLocalizer through C2's stub buffer."
    ),
    small_bullet(
        "<b>Evening:</b> fix Modal secret <i>WANDB_ENTITY</i> (currently djrgvc; should be d-grant-uc-berkeley) "
        "so the runtime override in <i>modal_app.py::train_remote</i> can be removed."
    ),
    small_bullet(
        "<b>Stretch:</b> reproduce Sharony's &quot;modified-game&quot; ablation (color-permuted blocks) "
        "on Fetch &mdash; a cheap signal that the VLM is doing semantic work, not pixel statistics."
    ),

    Spacer(1, 0.08 * inch),
    Paragraph("Risks we are watching", H2),
    small_bullet(
        "<b>HER may already saturate Fetch.</b> If A1's HER baselines hit ~95% across all three envs, "
        "there is no headroom for Semantic PER to show improvement on Fetch alone. "
        "Fallback: harder tasks (MetaWorld, FetchPickAndPlaceDense) and/or sample-efficiency framing instead of asymptotic success."
    ),
    small_bullet(
        "<b>VLM 3D grounding noise (Path C).</b> If GPT-4o's coordinate error is &gt; 5 cm, "
        "synthetic CF-relabels collapse to zero-reward transitions. Confidence threshold and oracle-CF upper-bound contain the risk."
    ),
    small_bullet(
        "<b>Statistical headroom.</b> All current numbers are 3 seeds with sigma 0.1&ndash;0.4. "
        "Headline claims need at least 5 seeds and a paired test for the paper."
    ),
]

story.append(PageBreak())

# =====================================================================
# PAGE 5 -- Bibliography highlights from L2
# =====================================================================
story += [
    Paragraph("Bibliography highlights (L2)", H1),
    Paragraph(
        "Full annotated bibliography in <i>agent_reports/L2_bibliography.md</i> (15+ papers across "
        "three threads: credit assignment, HER SOTA, VLM-in-RL). The highest-leverage citations:",
        BODY_J),
    hr(),

    Paragraph("Direct competitors / must-cite", H2),
    small_bullet(
        "<b>Sharony et&nbsp;al. 2026</b> (arXiv:2602.01915) &mdash; VLM-Guided Experience Replay. "
        "Closest concurrent work; differentiation handled in detail on page 3."
    ),
    small_bullet(
        "<b>Ozgur et&nbsp;al. 2025</b> (arXiv:2504.11247, &quot;Next-Future&quot;) &mdash; principled single-step replacement for HER's future strategy. "
        "Sample-efficiency gains on 7/8 manipulation tasks. <b>MUST cite</b> as a 2025 HER replacement baseline."
    ),
    small_bullet(
        "<b>Sayar et&nbsp;al. 2023</b> (arXiv:2312.02677, &quot;Contact Energy Hindsight&quot;) &mdash; prioritizes contact-rich transitions. "
        "Same family as ours; we substitute VLM-causal localization for contact-energy heuristics."
    ),
    small_bullet(
        "<b>Chuck et&nbsp;al. 2025</b> (ICLR, &quot;HInt / NCII&quot;) &mdash; counterfactual <i>object-interaction</i> nulling for HER relabeling. "
        "Closest to Path C in spirit; uses a learned dynamics model rather than a VLM."
    ),

    Paragraph("Credit assignment lineage", H2),
    small_bullet(
        "<b>Pignatelli et&nbsp;al. 2023</b> (arXiv:2312.01072) &mdash; survey of temporal credit assignment in deep RL. "
        "Anchor citation for our framing."
    ),
    small_bullet(
        "<b>Mesnard et&nbsp;al. 2021</b> (ICML, &quot;Counterfactual Credit Assignment&quot;) &mdash; foundational future-conditional baselines. "
        "Formal precursor for Path C's &quot;VLM as counterfactual oracle&quot;."
    ),
    small_bullet(
        "<b>Arjona-Medina et&nbsp;al. 2019</b> (NeurIPS, &quot;RUDDER&quot;) &mdash; return decomposition via LSTM contribution analysis. "
        "Conceptual ancestor for failure-localized PER weighting."
    ),

    Paragraph("VLM / language in RL", H2),
    small_bullet(
        "<b>Rocamonde et&nbsp;al. 2023</b> &mdash; VLMs as zero-shot reward models. "
        "Adjacent (VLM-as-reward, not VLM-as-replay)."
    ),
    small_bullet(
        "<b>Baumli et&nbsp;al. 2023</b>, <b>Code-as-Reward</b> (Venuto et&nbsp;al. 2024) &mdash; further VLM-as-reward variants."
    ),
    small_bullet(
        "<b>CAST</b> (Glossop, Levine et&nbsp;al., arXiv:2508.13446) &mdash; counterfactual <i>language</i> labels for VLA imitation. "
        "Different problem; useful as a contrasting use of &quot;VLM counterfactual&quot; terminology."
    ),

    Spacer(1, 0.10 * inch),
    hr(),
    Paragraph(
        "Sources in this deck: agent reports A1, A2, C1, C2, L1, L2 in "
        "<i>agent_reports/</i>. Final ablation numbers replicated verbatim from project README.md results table.",
        META),
]

# =====================================================================
# PAGE 6 -- N3 Bayesian framing (if landed)
# =====================================================================
if HAS_N3:
    story.append(PageBreak())
    story += [
        Paragraph("Theoretical Motivation &mdash; Semantic PER as IS Posterior Reweighting", H1),
        Paragraph(
            "Agent N3 (theoretical framing). Source: <i>agent_reports/N3_bayesian_framing.md</i>.",
            META,
        ),
        hr(),

        Paragraph("TL;DR", H2),
        small_bullet(
            "<b>The whole VLM-in-replay paradigm</b> &mdash; ours and Sharony's &mdash; is most cleanly read as "
            "<i>importance-sampled stochastic optimization with the VLM as a learned proposal distribution.</i> "
            "The VLM emits a posterior <i>q&#x03C6;(t* | &tau;)</i> over which transitions are responsible for an episode's outcome."
        ),
        small_bullet(
            "<b>Semantic PER is multiplicative posterior reweighting</b> on the standard PER proposal. "
            "Sharony's mixture is additive convex combination of a VLM proposal with uniform replay &mdash; "
            "in the limit &lambda; = 1 it <i>discards TD-error entirely</i>; in the limit w_max = 1 we recover PER exactly."
        ),
        small_bullet(
            "<b>Headline equation:</b> &mu;_Sem(i) &prop; &mu;_P(i) &middot; w_sem(i; &tau;), where "
            "w_sem(i; &tau;) = E_{t* ~ q&#x03C6;}[K_W(i; t*)] is the expected window-kernel mass the VLM places on transition i. "
            "This factorises priority into a <i>learning-progress</i> term |&delta;_i|<sup>&alpha;</sup> and a <i>causal-influence</i> term w_sem."
        ),
        small_bullet(
            "<b>Why this matters for the paper:</b> recasts our headline from "
            "<i>&quot;VLM-PER beats PER by X%&quot;</i> to <i>&quot;foundation-model priors are sufficient credit-assignment oracles for "
            "sparse-reward manipulation&quot;</i> &mdash; a thesis, not a benchmark. "
            "Predicts diagnostics (ESS of w_sem; KL of q&#x03C6; vs heuristic Oracle) Sharony cannot produce."
        ),

        Spacer(1, 0.06 * inch),
        Paragraph("Where semantic PER sits in the IS-correction taxonomy", H2),
        small_bullet(
            "<b>Prioritized DQN</b> (Schaul 2016): proposal &mu;_P &prop; |&delta;|<sup>&alpha;</sup>; correction is per-sample w_IS = (|D_B|&middot;&mu;_P)<sup>&minus;&beta;</sup>."
        ),
        small_bullet(
            "<b>Retrace / V-trace</b>: proposal is behaviour policy; correction is clipped per-step IS ratios. Bias-variance via truncation."
        ),
        small_bullet(
            "<b>Semantic PER (ours):</b> proposal &mu;_Sem &prop; |&delta;|<sup>&alpha;</sup> &middot; w_sem; we currently use w_IS,P "
            "(under-corrected, analogous to V-trace's truncation). Bias source: VLM miscalibration plus under-correction &mdash; "
            "principled to disclose, not a fatal flaw."
        ),
        small_bullet(
            "<b>Sharony (VLM-RB):</b> &lambda;<sub>t</sub>&middot;&mu;_VLM + (1&minus;&lambda;<sub>t</sub>)&middot;&mu;_U; no published IS correction. "
            "Their mixture targets a <i>different</i> objective than PER; ours stays inside the PER objective family."
        ),

        Spacer(1, 0.06 * inch),
        Paragraph("New ablations the framing suggests", H2),
        small_bullet(
            "<b>Temperature-controlled posterior:</b> prompt the VLM for a soft distribution over t*, not a single argmax. "
            "Predict robustness on tasks where the VLM is uncertain."
        ),
        small_bullet(
            "<b>IS-correction ablation:</b> w_IS,P vs w_IS,Sem &mdash; quantify the under-correction bias directly."
        ),
        small_bullet(
            "<b>ESS / KL diagnostics:</b> track effective sample size of w_sem; KL(p_oracle || q&#x03C6;) on heuristic-Oracle episodes. "
            "Operationalises the Bayesian framing as measurable quantities."
        ),
    ]

# =====================================================================
# PAGE 7 -- N1 Verifiable Counterfactuals (if landed)
# =====================================================================
if HAS_N1:
    story.append(PageBreak())
    story += [
        Paragraph("Verifiable Counterfactuals &mdash; Closing the Teleport-Collapse Loophole", H1),
        Paragraph(
            "Agent N1 (novel direction). Source: <i>agent_reports/N1_verifiable_counterfactuals.md</i>, "
            "smoke results in <i>N1_smoke_results.json</i>, code at <i>src/vlm/verified_counterfactual.py</i>.",
            META,
        ),
        hr(),

        Paragraph("Mechanism", H2),
        small_bullet(
            "<b>Path C's headline failure mode (C1):</b> on FetchPush, the &quot;achieved_goal&quot; prompt collapses to "
            "<i>corrective_position == desired_goal</i> in ~50% of episodes &mdash; the VLM proposes <b>teleporting the block to the target</b>. "
            "C1 papered over this with a 5 cm gate; that is a heuristic, not a mechanism."
        ),
        small_bullet(
            "<b>The new mechanism:</b> ask the VLM for a corrective <i>action sequence</i> at failure timestep K, "
            "execute it in a <b>fresh fork of the simulator</b> restored to s_K via MuJoCo qpos/qvel/mocap snapshot, "
            "and accept only if the env's own sparse reward fires within 50 steps. "
            "<b>Teleport is structurally inexpressible</b> as a 4-vector action &mdash; the failure mode is eliminated by construction."
        ),
        small_bullet(
            "<b>Verified counterfactuals carry confidence 1.0 by definition</b> &mdash; the env itself signed off. "
            "Off-policy correctness preserved: the value function still trains on the real reward function, not a VLM surrogate. "
            "Compare to reward shaping (warps the value target) or imagined-goal HER (zero-reward synthetic transitions on bad VLM coords)."
        ),

        Spacer(1, 0.06 * inch),
        Paragraph("Smoke results (4/4 PASS, 17.6 ms / verification)", H2),
        small_bullet(
            "<b>#1 Teleport case</b> (FetchPush seed 1251, achieved_goal variant, no action): "
            "rejected with reason <i>no_corrective_action_provided</i> &mdash; structural rejection of the teleport pathology."
        ),
        small_bullet(
            "<b>#2 Action CF on PickAndPlace</b> (seed 2234): VLM action runs end-to-end, "
            "rejected at final_distance = 0.316 m (goal_not_reached). The mechanism handled an honestly-bad VLM proposal correctly."
        ),
        small_bullet(
            "<b>#3 Composite &quot;all&quot; variant</b> (PickAndPlace seed 9095): runs end-to-end, "
            "rejected at final_distance = 0.164 m. Same path; same correct rejection."
        ),
        small_bullet(
            "<b>#4 Hand-crafted success case</b> (PickAndPlace, goal moved 3 cm toward block, unit action): "
            "<b>verified at step 0</b> with final_distance = 0.030 m &mdash; proves the accept path works end-to-end."
        ),

        Spacer(1, 0.06 * inch),
        Paragraph("Implications for the paper", H2),
        small_bullet(
            "Reframes Path C's headline from <i>&quot;VLM hindsight relabeling with imagined goals&quot;</i> to "
            "<b>&quot;VLM-Verified Counterfactual Hindsight: a language prior with a physics-grounded acceptance test.&quot;</b> "
            "Sits adjacent to model-predictive control with a language prior, but is closer to a <i>test</i> than a <i>search</i>."
        ),
        small_bullet(
            "Removes Path C's main reviewer-killer (&quot;your VLM produced a physically impossible relabel&quot;) by construction. "
            "Buffer integration is a 50-LOC follow-on subclassing C2's CounterfactualHERBuffer stub &mdash; out of scope for tonight."
        ),
    ]

# =====================================================================
# PAGE 8 -- N2 cross-task transfer (if landed)
# =====================================================================
if HAS_N2:
    story.append(PageBreak())
    n2_source_line = (
        "Source: <i>agent_reports/N2_cross_task_transfer.md</i>, "
        "validation outputs in <i>N2_cross_task_validation_outputs.json</i>."
        if HAS_N2_MD else
        "Source: <i>agent_reports/N2_cross_task_validation_outputs.json</i> "
        "(report .md still in flight; figures pending)."
    )
    story += [
        Paragraph("Cross-Task VLM Transferability", H1),
        Paragraph(
            "Agent N2 (novel direction). " + n2_source_line,
            META,
        ),
        hr(),

        Paragraph("Headline claim &amp; pilot results", H2),
        small_bullet(
            "<b>Claim:</b> a <i>single prompt template</i> (one Python f-string with {task_description} interpolated) "
            "produces semantically-correct failure annotations across Push, PickAndPlace, and Slide &mdash; "
            "where any <i>learned</i> task-specific priority head (TD-error, contact-energy, fitted classifier) would require per-task retraining."
        ),
        small_bullet(
            "<b>12-episode pilot:</b> 4 episodes / env on FetchPush, FetchPickAndPlace, FetchSlide. "
            "<b>12/12 parse rate</b> (100% structured-JSON output), "
            "<b>12/12 task-relevant</b> annotations (Claude Opus 4.7 judge with env-specific rubric), "
            "tolerant keyframe agreement <b>50% Push, 75% PickPlace, 100% Slide</b> &mdash; "
            "monotonic in failure visual-distinctiveness, exactly as predicted."
        ),
        small_bullet(
            "<b>Reference oracle:</b> heuristic <i>GoalDistanceLocalizer</i> (ballistic-throw + closest-approach, two-phase) "
            "on privileged sim state, no VLM calls. The VLM stands in for any zero-shot foundation-model prior."
        ),

        Spacer(1, 0.06 * inch),
        Paragraph("Why this strengthens the paper", H2),
        small_bullet(
            "<b>Paper-grade differentiation from Sharony:</b> the strongest claim is not failure-vs-success direction "
            "(L1 already covers that) but a <i>structural property of the VLM signal</i> &mdash; one prompt, three tasks, no retraining. "
            "Sharony evaluates on MiniGrid + OGBench, not manipulation; this transfer pattern is novel to our work."
        ),
        small_bullet(
            "Synergistic with N3's Bayesian framing: if q&#x03C6;(t* | &tau;) is informative across multiple Fetch tasks the VLM has not been "
            "task-fine-tuned for, the &quot;foundation-model prior as credit-assignment oracle&quot; thesis is operationalised, not asserted."
        ),
        small_bullet(
            "<b>Pre-registered next step:</b> 200-episode PickAndPlace sweep + downstream task-agnostic head training. "
            "Falsifiers in N2 &sect;4: parse-rate &lt; 80%, judge task-relevant &lt; 60%, or non-monotonic tolerant agreement &mdash; "
            "any would kill the claim cleanly."
        ),
    ]
    if HAS_N2_FIG:
        story += [
            Spacer(1, 0.06 * inch),
            img("figN2_cross_task_transfer.png", w=7.0,
                caption="N2 cross-task validation: VLM keyframe-agreement with the heuristic oracle across "
                        "FetchPush, FetchPickAndPlace, FetchSlide (Claude Opus 4.7, K=5 uniform keyframes, 4 episodes/env). "
                        "Source: agent_reports/figs/figN2_cross_task_transfer.png"),
        ]

# =====================================================================
# PAGE 9 -- C1v2-B real-data validation (if landed)
# =====================================================================
if HAS_C1V2_REAL:
    story.append(PageBreak())
    story += [
        Paragraph("Path C on Real Training Failures (C1v2-B)", H1),
        Paragraph(
            "Agent C1v2-B (real-data validation). Source: " + (
                "<i>agent_reports/C1v2_real_data.md</i>." if HAS_C1V2_REAL_MD
                else "real-policy failed-episode pickles in <i>agent_reports/c1v2_real_episodes_*.pkl</i>; .md report still in flight."
            ),
            META,
        ),
        hr(),
        Paragraph("Why this matters", H2),
        small_bullet(
            "C1's original prompts were tuned on <b>synthetic</b> failed episodes from a heuristic policy. "
            "C1v2-B re-runs the prompts on <b>failed episodes from real SAC training</b> "
            "(<i>c1v2_real_episodes_pickandplace.pkl</i>, <i>c1v2_real_episodes_push.pkl</i>) &mdash; this is the distribution the VLM "
            "will actually be queried on during a Semantic-PER run."
        ),
        small_bullet(
            "Real failures differ from synthetic in two ways: (a) policy-trajectory failures are typically <i>more subtle</i> "
            "(grasp slip, premature lift), not the gross misses the heuristic produces; (b) they have non-trivial state coverage "
            "of the goal region, so the &quot;teleport&quot; pathology has less room to operate."
        ),
    ]
    # If a real-vs-synthetic figure exists, drop it inline
    real_figs = sorted([p.name for p in FIGS.glob("figC1v2_real*.png")]) + \
                sorted([p.name for p in FIGS.glob("figC1v2B*.png")])
    if real_figs:
        story += [
            Spacer(1, 0.06 * inch),
            img(real_figs[0], w=7.0,
                caption="Real-data validation: VLM plausibility and specificity on real SAC failures vs synthetic. "
                        "Source: agent_reports/figs/" + real_figs[0]),
        ]
    else:
        story.append(small_bullet(
            "<b>Figure pending:</b> the real-vs-synthetic comparison plot has not yet been rendered "
            "(pickles on disk but no <i>figC1v2_real*</i> yet). "
            "This page will pick it up automatically once the figure lands."
        ))

doc.build(story)
print(f"wrote {OUT}")
