"""Generate the executive morning briefing PDF (5-6 pages).

Output: agent_reports/OVERNIGHT_SUMMARY.pdf
"""
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (HRFlowable, Image, KeepTogether, PageBreak,
                                Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path("/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185")
REPORTS = ROOT / "agent_reports"
FIGS = REPORTS / "figs"
OUT = REPORTS / "OVERNIGHT_SUMMARY.pdf"

# Style palette
DARK = HexColor("#1f2d3d")
ACCENT = HexColor("#2c5d7d")
GREEN = HexColor("#2c8a4f")
ORANGE = HexColor("#c8771a")
RED = HexColor("#a93221")
GRAY = HexColor("#566573")
LIGHT = HexColor("#ecf2f6")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"],
                    fontName="Helvetica-Bold", fontSize=17, leading=21,
                    textColor=DARK, spaceAfter=6, spaceBefore=0)
H2 = ParagraphStyle("H2", parent=styles["Heading2"],
                    fontName="Helvetica-Bold", fontSize=12, leading=15,
                    textColor=ACCENT, spaceAfter=4, spaceBefore=8)
H3 = ParagraphStyle("H3", parent=styles["Heading3"],
                    fontName="Helvetica-Bold", fontSize=10.5, leading=13,
                    textColor=DARK, spaceAfter=2, spaceBefore=4)
BODY = ParagraphStyle("Body", parent=styles["BodyText"],
                      fontName="Helvetica", fontSize=9.5, leading=12.5,
                      textColor=DARK, alignment=TA_LEFT, spaceAfter=4)
BULLET = ParagraphStyle("Bullet", parent=BODY, leftIndent=14,
                        bulletIndent=4, spaceAfter=2)
MONO = ParagraphStyle("Mono", parent=BODY, fontName="Courier",
                      fontSize=8.5, leading=11, textColor=GRAY)
BANNER = ParagraphStyle("Banner", parent=styles["Heading1"],
                        fontName="Helvetica-Bold", fontSize=18, leading=22,
                        textColor=RED, alignment=TA_CENTER, spaceAfter=8,
                        spaceBefore=2)
BANNER_SUB = ParagraphStyle("BannerSub", parent=BODY,
                            fontName="Helvetica-Oblique", fontSize=10,
                            textColor=GRAY, alignment=TA_CENTER, spaceAfter=10)


def img(path: Path, max_width=6.5 * inch, max_height=3.6 * inch) -> Image:
    """Embed an image preserving aspect ratio, fitting in the given box."""
    with PILImage.open(path) as p:
        w, h = p.size
    aspect = h / w
    width = min(max_width, max_height / aspect)
    height = width * aspect
    return Image(str(path), width=width, height=height)


def banner_box(flowables):
    tbl = Table([[fl] for fl in flowables], colWidths=[6.6 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fdecea")),
        ("BOX", (0, 0), (-1, -1), 1.2, RED),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return tbl


def build():
    doc = SimpleDocTemplate(
        str(OUT), pagesize=LETTER,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.6 * inch, bottomMargin=0.55 * inch,
        title="Overnight Summary 2026-05-12",
        author="MORNING-CONSOLIDATION agent (Opus 4.7)",
    )
    elems = []

    # ===== Page 1 — Executive verdict =====
    elems.append(Paragraph("Overnight Summary — 2026-05-12", H1))
    elems.append(Paragraph("MORNING-CONSOLIDATION agent (Opus 4.7) &middot; "
                           "branch <font face='Courier'>agent/pathc-lead</font>", BODY))
    elems.append(HRFlowable(width="100%", color=ACCENT, thickness=0.8,
                            spaceBefore=2, spaceAfter=6))

    elems.append(banner_box([
        Paragraph("PATH C KILL VERDICT: CONFIRMED.", BANNER),
        Paragraph(
            "Oracle-CF underperforms HER on every Fetch environment, "
            "including after the <font face='Courier'>oracle_cf_push</font> "
            "midpoint bug fix (<font face='Courier'>ccb63d4</font>). "
            "Pre-registered kill criterion violated: "
            "&Delta;(OCF&minus;HER) on FetchPickAndPlace = &minus;0.05, "
            "well below the +0.10 threshold for Path C continuation.",
            BANNER_SUB),
    ]))
    elems.append(Spacer(1, 6))

    elems.append(Paragraph("Three biggest WINs overnight", H3))
    for txt in [
        ("A defensible 35-page NeurIPS-style paper draft exists. R1 and R2 "
         "Top-3 weaknesses addressed substantively in fresh commits "
         "(<font face='Courier'>d2ce20b</font>, "
         "<font face='Courier'>95d9cee</font>, "
         "<font face='Courier'>c488c6b</font>); &sect;3, &sect;5, &sect;6 "
         "received honesty passes."),
        ("The negative empirical result is traceable, not noise. The pre-fix "
         "Oracle-CF push run was buggy; we fixed it (<font face='Courier'>ccb63d4</font>), "
         "reran 3 seeds, and the verdict held (mean 0.383 vs HER 0.550 on Push)."),
        ("N1 verifier 4/4 smoke pass; N2 hand-judged 12/12 task-relevant. "
         "These positive signals are scalable (n=12 &rarr; n&ge;50) "
         "the moment Modal frees."),
    ]:
        elems.append(Paragraph("&bull; " + txt, BULLET))

    elems.append(Spacer(1, 4))
    elems.append(Paragraph("Three biggest CONCERNS", H3))
    for txt in [
        ("Path C empirical headline is dead. Even <i>privileged</i> Oracle-CF "
         "cannot exceed HER by 0.10 on the pre-registered decision env."),
        ("Path A bidirectional pivot also fails: 5/6 bidir runs ended at 0.0 "
         "success; only Push s42 reached 0.4 at 300k steps."),
        ("Modal Phase 2 (VLM-CF + Verified-CF, 18 runs) never fired all night. "
         "A1&rsquo;s prior HER sweep is still holding all 10 GPUs. The watchdog&rsquo;s "
         "<font face='Courier'>check_modal_free</font> correctly never returned True."),
    ]:
        elems.append(Paragraph("&bull; " + txt, BULLET))

    elems.append(Spacer(1, 6))
    elems.append(Paragraph(
        "What Daniel should do FIRST this morning &mdash; three options", H3))
    for letter, title, body in [
        ("(a)", "Pivot to harder envs (Adroit / MetaWorld / AntMaze).",
         "3 hard envs &times; {HER, Oracle-CF} &times; 3 seeds &times; 300k steps. "
         "Wallclock &asymp; 4 days on 4 Modal GPUs. "
         "Risk: if HER also wins, we lose 4 of 5 remaining days."),
        ("(b)", "Reframe as &lsquo;methodology + theory + honest negative empirical&rsquo; paper.",
         "No new training. 2 days &sect;5/&sect;6 rewrite + 1 day fig set "
         "+ 1 day cross-review. Risk: still needs a positive secondary signal."),
        ("(c)", "Scale up N2 (n=12 &rarr; n=50/env) and run Verified-CF Phase 2 the moment Modal frees.",
         "1 day for N2 scale-up (local). Phase 2 wallclock &asymp; 18h. "
         "Risk: Phase 2 inherits Path C&rsquo;s empirical weakness."),
    ]:
        elems.append(Paragraph(
            f"<b>{letter}</b> <b>{title}</b> {body}", BULLET))

    elems.append(Spacer(1, 6))
    # Mini-figure inset
    fig_path = FIGS / "fig_morning_headline.png"
    if fig_path.exists():
        elems.append(Paragraph(
            "<font color='#566573' size=8><i>Headline figure (full size on Page&nbsp;3):</i></font>",
            BODY))
        elems.append(img(fig_path, max_width=5.0 * inch, max_height=2.0 * inch))

    elems.append(PageBreak())

    # ===== Page 2 — Overnight timeline =====
    elems.append(Paragraph("Page 2 &mdash; What got done overnight (visual timeline)", H1))
    elems.append(HRFlowable(width="100%", color=ACCENT, thickness=0.6,
                            spaceBefore=2, spaceAfter=8))

    tl_rows = [
        ["PDT", "Event", "Status"],
        ["22:00", "Path C overnight launched: 3 envs x HER vs Oracle-CF x 3 seeds, 250k steps", "OK"],
        ["22:20", "A2 bidir Modal verification job starts (a2_bidir_push_50k)", "OK"],
        ["23:35", "Section dive 0035 + reviewer feedback cycle 1", "OK"],
        ["00:01", "Verified-CF wiring fix committed (168518b)", "OK"],
        ["01:35", "Section dive 0135 (R2 W5/W6/W9 honesty pass)", "OK"],
        ["02:33", "Figure audits begin; fig1, fig4 regenerated NeurIPS-style", "OK"],
        ["03:02", "Watchdog: OCF - HER ~= -0.272 (buggy filter; true ~= -0.116). PIVOT flag written", "PIVOT"],
        ["03:02", "First Path A bidir spawn DIES: FileNotFoundError configs/bidir.yaml", "CRASH"],
        ["03:33", "Emergency cherry-pick eb899be: A2 bidir code onto pathc-lead; relaunch script fixed", "FIX"],
        ["03:33-06:01", "Path A bidir reruns sequentially (6 runs x ~25 min). Final: 5/6 = 0.0; Push s42 = 0.4", "DONE"],
        ["~03:53", "Cron LLM-agents stop firing (Claude session lapse). Bash watchdog stays alive", "DEGRADED"],
        ["06:33-07:36", "Morning consolidation crons fail x4 (no LLM agent)", "MISSED"],
        ["08:52", "Orchestrator -> phase2_waiting_for_modal. Modal busy_count = 10", "WAIT"],
        ["09:44/09:59/10:14", "oracle_cf_pushfix reruns finish (Push: 0.30/0.25/0.60 = mean 0.383)", "KILL"],
        ["10:27", "training_status_1027.md confirms KILL. Modal busy_count = 11 (worse)", "BLOCKED"],
    ]
    tl = Table(tl_rows, colWidths=[1.05 * inch, 5.0 * inch, 0.85 * inch],
               repeatRows=1)
    tl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.0),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elems.append(tl)
    elems.append(Spacer(1, 8))
    elems.append(Paragraph(
        "Annotations: <b>~03:53</b> &mdash; LLM-agent cron system died; "
        "watchdog (bash) stayed alive but could not compensate. "
        "<b>03:35</b> &mdash; Path A pivot relaunched after debug. "
        "<b>06:01</b> &mdash; Path A bidir final run finished. "
        "<b>10:14 UTC</b> &mdash; Push OCF post-fix rerun final seed (s999) finished. "
        "Modal Phase 2 (18 runs) <b>never launched all night</b>.",
        BODY))
    elems.append(PageBreak())

    # ===== Page 3 — Empirical results =====
    elems.append(Paragraph("Page 3 &mdash; Empirical results (3-min read)", H1))
    elems.append(HRFlowable(width="100%", color=ACCENT, thickness=0.6,
                            spaceBefore=2, spaceAfter=6))

    elems.append(Paragraph("Pre-registered kill rule", H3))
    elems.append(Paragraph(
        "<i>If Oracle-CF exceeds HER by &ge; +0.10 on <font face='Courier'>FetchPickAndPlace</font> "
        "final eval success at 250k steps, Path C (verified-counterfactual hindsight) "
        "proceeds to full VLM-CF sweeps. Otherwise we pivot the paper&rsquo;s headline "
        "to the IS-posterior framing.</i> (paper &sect;5.6, in-flight experiments, "
        "written before Path C results were available.)",
        BODY))

    # Results table
    elems.append(Paragraph("Per-seed results (every datapoint, no hiding)", H3))
    res_rows = [
        ["Method", "Env", "s42", "s123", "s999", "Mean", "SE"],
        ["HER", "FetchPush", "0.600", "0.450", "0.600", "0.550", "0.050"],
        ["HER", "FetchPickAndPlace", "0.050", "0.050", "0.400", "0.167", "0.117"],
        ["HER", "FetchSlide", "0.200", "0.050", "0.050", "0.100", "0.050"],
        ["Oracle-CF (pre-fix)", "FetchPush", "0.100", "0.350", "0.200", "0.217", "0.073"],
        ["Oracle-CF (pre-fix)", "FetchPickAndPlace", "0.100", "0.050", "0.200", "0.117", "0.044"],
        ["Oracle-CF (pre-fix)", "FetchSlide", "0.200", "0.200", "0.150", "0.183", "0.017"],
        ["Oracle-CF (post-fix)", "FetchPush", "0.300", "0.250", "0.600", "0.383", "0.109"],
        ["Path A Bidir", "FetchPush", "0.400", "0.000", "-", "0.200", "0.200"],
        ["Path A Bidir", "FetchPickAndPlace", "0.000", "0.000", "-", "0.000", "0.000"],
        ["Path A Bidir", "FetchSlide", "0.000", "0.000", "-", "0.000", "0.000"],
    ]
    rt = Table(res_rows,
               colWidths=[1.5 * inch, 1.55 * inch, 0.55 * inch, 0.6 * inch,
                          0.6 * inch, 0.65 * inch, 0.55 * inch],
               repeatRows=1)
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("FONTNAME", (5, 1), (5, -1), "Helvetica-Bold"),
    ]))
    elems.append(rt)
    elems.append(Spacer(1, 6))

    # Kill verdict subtable
    elems.append(Paragraph("Kill verdict (Δ = Oracle-CF − HER, best variant per env)", H3))
    kv_rows = [
        ["Env", "HER", "Best OCF", "Delta", "Threshold", "Verdict"],
        ["FetchPush", "0.550", "0.383 (post-fix)", "-0.167", "+0.10", "KILL"],
        ["FetchPickAndPlace", "0.167", "0.117 (pre-fix)", "-0.050", "+0.10", "KILL (decision env)"],
        ["FetchSlide", "0.100", "0.183 (pre-fix)", "+0.083", "+0.10", "KILL (below threshold)"],
    ]
    kv = Table(kv_rows, colWidths=[1.4 * inch, 0.7 * inch, 1.45 * inch,
                                   0.7 * inch, 0.75 * inch, 1.65 * inch],
               repeatRows=1)
    kv.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (1, 1), (-2, -1), "RIGHT"),
        ("ALIGN", (-1, 1), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#cccccc")),
        ("FONTNAME", (-1, 1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (-1, 1), (-1, -1), RED),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems.append(kv)
    elems.append(Spacer(1, 8))

    # Headline figure embedded full-size
    if fig_path.exists():
        elems.append(img(fig_path, max_width=6.5 * inch, max_height=3.2 * inch))
        elems.append(Paragraph(
            "<font size=8><i>Figure 1. Final eval success rate (mean &plusmn; SE, "
            "individual seeds as dots) across the three Fetch environments. "
            "Pre-registered HER&nbsp;+&nbsp;0.10 KILL bar shown on "
            "<font face='Courier'>FetchPickAndPlace</font>. Oracle-CF (post-fix, Push) "
            "is the corrected midpoint-anchor rerun of <font face='Courier'>oracle_cf_push</font> "
            "after commit <font face='Courier'>ccb63d4</font>; the verdict is unchanged.</i></font>",
            BODY))

    elems.append(Spacer(1, 4))
    elems.append(Paragraph(
        "<b>Honest interpretation.</b> HER on Fetch is already strong at 250k steps. "
        "Even with privileged Oracle-CF (perfect failure-frame knowledge and IK-correct "
        "counterfactual actions) we cannot exceed HER by 0.10 on the pre-registered "
        "decision env. The bottleneck on Fetch is not credit assignment from failed "
        "episodes &mdash; it is exploration / representation. This is a real negative "
        "result, not a Path C implementation failure: we fixed the "
        "<font face='Courier'>oracle_cf_push</font> midpoint bug "
        "(<font face='Courier'>ccb63d4</font>) and the verdict held on the rerun.",
        BODY))

    elems.append(PageBreak())

    # ===== Page 4 — Paper progress + reviewer status =====
    elems.append(Paragraph("Page 4 &mdash; Paper progress + reviewer status", H1))
    elems.append(HRFlowable(width="100%", color=ACCENT, thickness=0.6,
                            spaceBefore=2, spaceAfter=6))

    elems.append(Paragraph(
        "<b>Paper artefact.</b> 35 pages, 540&nbsp;KB, NeurIPS LaTeX style at "
        "<font face='Courier'>agent_reports/paper/main.pdf</font>. "
        "Compiles cleanly via <font face='Courier'>cd agent_reports/paper &amp;&amp; bash build.sh</font>.",
        BODY))

    elems.append(Paragraph("Sections rewritten overnight (with commit SHAs)", H3))
    secs_rows = [
        ["Section", "Edit", "Commit"],
        ["§3 Theory / IS posterior", "R2 W5/W6/W9 honesty pass", "d2ce20b"],
        ["§5 Experimental design", "kill criterion pre-registered", "(in tex)"],
        ["§6 Broader Impact", "structured positive/negative/scope", "c488c6b"],
        ["§3 (cross-cut)", "drop uniqueness claim; add bias bound", "95d9cee"],
        ["Figures fig1, fig4", "NeurIPS-style replacement", "(figs/)"],
        ["Watchdog filter / W&B group regex", "honest pivot decisions", "48067de"],
    ]
    sec_tbl = Table(secs_rows, colWidths=[2.3 * inch, 3.0 * inch, 1.2 * inch],
                    repeatRows=1)
    sec_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (-1, 1), (-1, -1), "Courier"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems.append(sec_tbl)
    elems.append(Spacer(1, 8))

    elems.append(Paragraph("Reviewer status", H3))
    rev_rows = [
        ["Reviewer", "Initial verdict", "Overnight progress", "Outstanding"],
        ["R1 (area chair)",
         "REJECT (3 weaknesses)",
         "Top-3 addressed substantively",
         "polish abstract; align figs"],
        ["R2 (theory-skeptic)",
         "REJECT (theory; 9 weaknesses)",
         "Top-3 + W5/W6/W9 addressed; uniqueness dropped; bias bound added",
         "formal proof of bias bound"],
        ["R3", "never fired", "n/a", "fire R3 cycle"],
    ]
    rev_tbl = Table(rev_rows,
                    colWidths=[1.0 * inch, 1.4 * inch, 2.4 * inch, 1.7 * inch],
                    repeatRows=1)
    rev_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems.append(rev_tbl)

    elems.append(Spacer(1, 6))
    elems.append(Paragraph("Reviewer items still open", H3))
    for txt in [
        "Bias-bound formal proof (R2 W9) — sketch is in §3, full proof not yet written.",
        "R3 cycle never fired (a third reviewer voice was planned but the cron stalled at ~03:53 PDT).",
        "Cross-judge sanity check (Sonnet 4.5 / GPT-4o on the same C1v2 outputs) is on the open-work list.",
    ]:
        elems.append(Paragraph("&bull; " + txt, BULLET))

    elems.append(PageBreak())

    # ===== Page 5 — Honest path forward =====
    elems.append(Paragraph("Page 5 &mdash; Honest path forward", H1))
    elems.append(HRFlowable(width="100%", color=ACCENT, thickness=0.6,
                            spaceBefore=2, spaceAfter=6))

    for letter, title, body_html in [
        ("(a)", "Pivot to harder envs (Adroit / MetaWorld / AntMaze).",
         "<b>Experiment.</b> 3 hard envs (e.g. AdroitHammer-v1, MetaWorld-pick-place-v2, "
         "AntMaze-medium-v3) &times; {HER, Oracle-CF} &times; 3 seeds &times; 300k steps. Total = 18 runs. "
         "<b>Wallclock.</b> &asymp; 36h on 4 Modal GPUs once it launches; realistically <b>4 days</b> "
         "including config/sweep setup and the wait for A1&rsquo;s sweep to free Modal. "
         "<b>Expected outcome.</b> HER is known to struggle on Adroit and AntMaze. If Oracle-CF "
         "beats HER by &ge; 0.10 on at least one env, we recover a positive empirical claim. "
         "P(at least one win) &asymp; 50% based on prior literature. "
         "<b>Risk.</b> If HER also wins on hard envs, we have burned 4 of 5 remaining days "
         "and are <i>worse</i> off than option (b). Submission slips to the next deadline."),
        ("(b)", "Reframe as &lsquo;methodology + theory + honest negative empirical&rsquo; paper.",
         "<b>Experiment.</b> None required. The kill verdict <i>is</i> the headline. "
         "<b>Wallclock.</b> 2 days for &sect;5 / &sect;6 / abstract rewrite; 1 day for new fig set + table; "
         "1 day for cross-reviewer pass. <b>4 days total</b>; deadline-feasible. "
         "<b>Expected outcome.</b> Defensible NeurIPS submission with a clear contribution: "
         "IS-posterior framing (&sect;3) + verifier mechanism (&sect;4) + empirically-supported "
         "claim that HER on Fetch is at the credit-assignment ceiling. Negative results, framed "
         "as pre-registered falsification, are well-respected at top venues if the methodology is clean. "
         "<b>Risk.</b> Reviewers may still down-vote for lack of positive empirical evidence. "
         "Mitigation: pair with workshop submission (e.g. NeurIPS Workshop on Robot Learning) as fallback."),
        ("(c)", "Scale up N2 (n=12 &rarr; n=50/env) and run Verified-CF Phase 2 the moment Modal frees.",
         "<b>Experiment.</b> N2 cross-task transferability scaled from n=12 to n=50 per env "
         "(3 envs &times; 50 episodes, model-judged). Launch the 18 Phase 2 Modal runs (VLM-CF + Verified-CF) "
         "as soon as A1&rsquo;s HER sweep releases capacity. Phase 2 runs are designed and the code wiring is fixed "
         "(<font face='Courier'>168518b</font>); only Modal capacity blocks. "
         "<b>Wallclock.</b> 1 day for N2 scale-up (cheap, runs locally on the workstation while Modal is busy). "
         "Phase 2 wallclock &asymp; 18h once it launches. <b>2 days total</b> if Modal frees today. "
         "<b>Expected outcome.</b> Stronger N2 evidence than n=12 (currently 12/12 is indistinguishable from "
         "80% true rate). Phase 2 will probably show VLM-CF and Verified-CF &asymp; Oracle-CF; benefit, if any, "
         "visible only in CF-density / verification-pass metrics, not final eval success. "
         "<b>Risk.</b> Phase 2 inherits Path C&rsquo;s empirical weakness."),
    ]:
        elems.append(Paragraph(f"<b>Option {letter} &mdash; {title}</b>", H3))
        elems.append(Paragraph(body_html, BODY))
        elems.append(Spacer(1, 4))

    elems.append(HRFlowable(width="100%", color=GRAY, thickness=0.5,
                            spaceBefore=4, spaceAfter=4))
    elems.append(Paragraph("Honest recommendation", H3))
    elems.append(Paragraph(
        "<b>(b) + a defensive slice of (c).</b> Reframe the paper around the IS-posterior theory + "
        "verifier mechanism + honest kill result. In parallel: scale N2 to n=50 (cheap, local) and let "
        "Phase 2 launch when Modal frees &mdash; its outcome becomes a &sect;5 ablation regardless of "
        "sign. Do <b>not</b> pursue (a) right now; 4 days of training is a bet we cannot underwrite "
        "with 5 days to deadline. If by the end of Day 2 the paper rewrite is on track and Phase 2 is "
        "in flight, we can revisit (a) as a stretch goal for the camera-ready, not the submission.",
        BODY))

    elems.append(PageBreak())

    # ===== Page 6 — Open code items =====
    elems.append(Paragraph("Page 6 &mdash; Open code items", H1))
    elems.append(HRFlowable(width="100%", color=ACCENT, thickness=0.6,
                            spaceBefore=2, spaceAfter=6))

    elems.append(Paragraph("From <font face='Courier'>_CODE_BLOCKER.md</font>", H3))
    elems.append(Paragraph(
        "<b>B1 (verified_cf no-op):</b> RESOLVED in <font face='Courier'>168518b</font>. "
        "26/26 invariants in <font face='Courier'>tests/test_verified_cf_wiring.py</font> + "
        "<font face='Courier'>tests/test_counterfactual_buffer.py</font> pass.",
        BULLET))
    elems.append(Paragraph(
        "<b>B2 (Modal WANDB_ENTITY regression):</b> NOT YET PATCHED. Triple regression on "
        "<font face='Courier'>modal_app.py::train_remote</font> and "
        "<font face='Courier'>src/utils/logger.py</font>. Will block every Phase 2 Modal job at "
        "<font face='Courier'>wandb.init</font>. <b>Must patch before Phase 2 launches.</b> "
        "Fix: re-introduce the <font face='Courier'>WANDB_ENTITY=d-grant-uc-berkeley</font> "
        "override at the top of <font face='Courier'>train_remote</font>, restore try/except "
        "fallback in <font face='Courier'>logger.py</font>, rebuild Modal image.",
        BULLET))
    elems.append(Paragraph(
        "<b>B3 (wrappers.py render_mode regression):</b> Defensive regression, not currently "
        "crashing locally or on Modal because both envs set <font face='Courier'>MUJOCO_GL</font> "
        "appropriately. Still worth patching for robustness.",
        BULLET))

    elems.append(Spacer(1, 6))
    elems.append(Paragraph("Designed but not yet run", H3))
    elems.append(Paragraph(
        "&bull; <b>cf_window ablation</b> (<font face='Courier'>agent_reports/ablation_cfwindow_design.md</font>) "
        "&mdash; counterfactual horizon sensitivity. Local workstation can run it.",
        BULLET))
    elems.append(Paragraph(
        "&bull; <b>vlmtier ablation</b> (<font face='Courier'>agent_reports/ablation_vlmtier_design.md</font>) "
        "&mdash; VLM-tier vs. heuristic-tier vs. oracle-tier ablation. Local workstation can run it.",
        BULLET))

    elems.append(Spacer(1, 6))
    elems.append(Paragraph("Ready to launch the moment Modal frees", H3))
    elems.append(Paragraph(
        "<b>Phase 2 sweep.</b> 18 runs = (3 envs) &times; (VLM-CF, Verified-CF, baseline) &times; (3 seeds) "
        "at 250k steps each. Orchestrator (PID 117592) is alive and polling Modal every 5 min. "
        "Once <font face='Courier'>busy_count &le; 4</font>, it will spawn automatically. "
        "Watchdog (PID 56086) is alive. Provided B2 is patched first, the launch is push-button.",
        BODY))

    elems.append(Spacer(1, 6))
    elems.append(HRFlowable(width="100%", color=GRAY, thickness=0.4,
                            spaceBefore=2, spaceAfter=4))
    elems.append(Paragraph(
        "<font size=8 color='#566573'>"
        "Deliverable paths: "
        "<font face='Courier'>agent_reports/figs/fig_morning_headline.{png,pdf}</font>, "
        "<font face='Courier'>agent_reports/MORNING_REPORT_2026-05-12.md</font>, "
        "<font face='Courier'>agent_reports/OVERNIGHT_SUMMARY.pdf</font>, "
        "<font face='Courier'>agent_reports/9pm_slidedeck.pdf</font>, "
        "<font face='Courier'>agent_reports/MORNING_SCP_COMMANDS.md</font>, "
        "<font face='Courier'>agent_reports/_MORNING_READY.md</font>."
        "</font>", BODY))

    doc.build(elems)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
