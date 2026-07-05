#!/usr/bin/env python3
"""Semantic layer: 5 reader-question chapters + bilingual operator-language strings.

The report used to be organized by methodology stage (18 numbered sections —
framing, estimation, policy, governance). Operators could not read it. The new
spine is the reader's five questions; every legacy section keeps its content
and anchor id but moves into the chapter that answers its question:

    ch1 拍板页    Do we spend or not?              (s0 TLDR + s1 memo + termination
                                                     + rejected options as "never do")
    ch2 这笔账    Why? How was the math done?      (s2 math + s3 product/price anchors)
    ch3 打法      Who, where, what message?        (s4 channels + s5 dimensions +
                                                     s6 heatmap + s7 h-main +
                                                     s12 KOL + s15 who NOT to touch)
    ch4 执行      Who does it, when, how much,
                  and how do we know we won?       (s8 gates/cards + s10 budget +
                                                     s11 plays + s14 tests + s17 checklist
                                                     — merged into unified task cards)
    ch5 底牌      Why believe this? What could
                  overturn it?                     (s9 challenges + s13 measurement +
                                                     s16 evidence + s18 roadmap)

Language: OPERATOR_STRINGS carries the decision-critical vocabulary in both
languages (must stay key-parallel; tests enforce it). ZH_BASE carries the full
legacy Chinese label set so zh configs no longer need to ship 340 labels.
Lookup order everywhere: cfg["labels"] override > OPERATOR_STRINGS[lang] >
ZH_BASE (zh only) > the English default written at the call site.

Jargon rule: the operator word leads, the methodology term follows in
parentheses on first use — "获客成本红线 (CAC ceiling)", never the reverse.
"""

from __future__ import annotations

from typing import Any

# ── Chapter spine ─────────────────────────────────────────────────────────────

CHAPTER_IDS = ("ch1", "ch2", "ch3", "ch4", "ch5")

# legacy section id -> owning chapter (anchors preserved for deep links)
SECTION_CHAPTER = {
    "s0": "ch1", "s1": "ch1", "term": "ch1",
    "s2": "ch2", "s3": "ch2",
    "s4": "ch3", "s5": "ch3", "s6": "ch3", "s7": "ch3", "s12": "ch3", "s15": "ch3",
    "s8": "ch4", "s10": "ch4", "s11": "ch4", "s14": "ch4", "s17": "ch4",
    "s9": "ch5", "s13": "ch5", "s16": "ch5", "s18": "ch5",
}

# depth modes, restated on the chapter spine
QUICK_CHAPTERS = {"ch1", "ch2"}
TERMINATION_CHAPTERS = {"ch1", "ch2", "ch5"}


# ── Decision-critical vocabulary (key-parallel across languages) ─────────────

OPERATOR_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # chapter banners: the question each chapter answers + answer templates
        "ch1_title": "1 · The Call",
        "ch1_question": "Do we spend money or not?",
        "ch2_title": "2 · The Money",
        "ch2_question": "Why? How was this math done?",
        "ch3_title": "3 · The Play",
        "ch3_question": "Who do we go after, where, and with what message?",
        "ch4_title": "4 · Execution",
        "ch4_question": "Who does what, by when, for how much — and how do we know we won?",
        "ch5_title": "5 · The Receipts",
        "ch5_question": "Why believe any of this? What could prove it wrong?",
        "ch_answer_label": "Short answer",
        # auto-answer templates (chapter banners)
        "ans_verdict_go": "Yes — spend, but release the budget stage by stage per chapter 4.",
        "ans_verdict_nogo": "No — the math does not work; do not spend on media.",
        "ans_verdict_conditional": "Not yet — do the zero-cost checks first, then decide at the checkpoint.",
        "ans_money": "Each sale earns {margin}; so acquiring one buyer may cost at most {ceiling} — {counts}.",
        "ans_money_counts": "{viable} channel(s) clearly profitable, {undetermined} unclear, {notviable} money-losing",
        "ans_play": "{channels} channel(s) worth testing; lead audiences: {dims}; {suppress} group(s) we must NOT touch.",
        "ans_execution": "{cards} task card(s), {blocked} frozen until data lands; every card carries a stop-loss line.",
        "ans_receipts": "{sourced} number(s) verified with links, {assumed} assumed (basis stated), {missing} still missing — weakest point: {weakest}",
        # verdict words (operator first, code in parens)
        "verdict_word_viable": "profitable (viable)",
        "verdict_word_not-viable": "money-losing (not-viable)",
        "verdict_word_undetermined": "unclear — get data first (undetermined)",
        "verdict_word_role-only": "support role only (role-only)",
        "verdict_big_go": "GO — SPEND",
        "verdict_big_no-go": "NO — DON'T SPEND",
        "verdict_big_conditional": "WAIT — CHECK FIRST",
        # heatmap grades
        "grade_H": "Main push",
        "grade_T": "Test",
        "grade_S": "Small bet",
        "grade_N": "Skip",
        "grade_A": "Never touch",
        # money vocabulary
        "cac_ceiling_word": "acquisition cost red line (CAC ceiling)",
        "unit_margin_word": "profit per unit sold",
        "kill_line_word": "Stop-loss line",
        "blocked_word": "FROZEN — no budget until",
        "gate_word": "Release condition",
        "owner_word": "Owner",
        "due_word": "Due",
        "success_word": "Success line",
        "never_do_heading": "Never do (under this math)",
        # provenance legend, in plain words
        "prov_legend": "Where every number comes from: ◆ verified (link attached) · ◇ assumed (basis written down) · ⊕ calculated (working shown) · ○ not yet obtained (we never invent numbers)",
        # auto chart captions
        "cac_caption": "How to read: bar past the red line = loses money · fully under = makes money · straddling = unclear, get data first. Here: {viable} profitable, {undetermined} unclear, {notviable} losing.",
        "heatmap_caption": "How to read: Main push = spend here first · Never touch = targeting these people burns money (they buy the cheaper SKU or would buy anyway).",
        # task cards
        "task_cards_heading": "Task cards (one card = one accountable move)",
        "other_tests_heading": "Stand-alone tests (not tied to a task card)",
        "test_in_card_label": "Test & stop-loss",
        "why_now_label": "Why now",
        # TOC
        "toc_title": "THE 5 QUESTIONS",
        # category-portfolio chapter answers
        "cat_ans_ch1": "{total} SKUs: {grow} Grow, {hold} Hold, {harvest} Harvest, {exit} Exit.",
        "cat_ans_ch2": "{total} findings — {critical} critical, {major} major, {watch} watch (severity capped by evidence grade).",
        "cat_ans_ch3": "{tiers} price tier(s) mapped across {skus} SKUs against the competitive set.",
        "cat_ans_ch4": "{n} SKU(s) verdicted Grow ({skus}) — confirm, then send to the single-SKU pipeline.",
        "cat_ans_ch1_invest": " Investment: fund {spend} {currency} for {units} incremental units and {profit} {currency} gross profit ({roi}x ROI); {never} cell(s) never funded.",
        "cat_ans_ch2_invest": " The spend above is ranked by marginal return and cut off at {lambda_star}x — the minimum acceptable return this cycle; see the frontier below.",
        "cat_ans_ch3_invest": " Of that, {n_cells} SKU × module combination(s) get funded this cycle — see the budget matrix below for exactly where.",
        "cat_ans_ch4_invest": " This cycle funds {n_cells} SKU × module activation(s) (see cards below); {never} cell(s) still need more evidence before they can be funded.",
        "cat_ans_ch5_invest": " Of the funded budget, {validated} cell(s) rest on a validated test, {mmm_calibrated} on MMM calibration, {assumption_grade} still assumption-grade. {mmm_note}",
        # investment dashboard (budget-frontier allocation, ref 06 policy-nbt)
        "inv_ch1_heading": "Where the investment budget goes",
        "inv_kpi_spend": "Recommended spend",
        "inv_kpi_units": "Incremental units",
        "inv_kpi_gross_profit": "Incremental gross profit",
        "inv_kpi_net_profit": "Net profit",
        "inv_kpi_roi": "ROI",
        "inv_kpi_lambda_star": "Cutoff return (λ*)",
        "inv_never_funded_heading": "Never funded this round",
        "inv_never_funded_empty": "Every eligible cell got funded.",
        "inv_reason_excluded_verdict": "SKU verdict excludes it (Harvest / Exit)",
        "inv_reason_confidence_blocked": "confidence blocked — tau_source missing or not measurement-ready",
        "inv_th_sku": "SKU",
        "inv_th_module": "Module",
        "inv_th_reason": "Why frozen",
        "inv_frontier_heading": "The budget-vs-return curve (frontier)",
        "inv_frontier_profit_title": "Cumulative gross profit as spend grows",
        "inv_frontier_roi_title": "Marginal ROI — return on the next unit of spend",
        "inv_frontier_caption": "How to read: follow the right-hand panel left to right — the dashed line marks where marginal ROI drops below the required return; funding stops there even if budget remains.",
        "inv_matrix_heading": "Where the money lands: SKU × module",
        "inv_matrix_caption": "How to read: darker cell = more spend; the dot color is the confidence badge — green = validated, blue = MMM-calibrated, amber = assumption-grade.",
        "inv_matrix_empty": "No allocation cleared the ROI floor.",
        "inv_th_spend": "Spend",
        "inv_th_roi": "ROI",
        "inv_tasks_heading": "Activation cards (this round's funded moves)",
        "inv_th_confidence": "Confidence",
        "inv_confidence_heading": "How much of this budget rests on solid evidence",
        "inv_confidence_validated": "Validated (randomized test + measurement gate)",
        "inv_confidence_mmm_calibrated": "MMM-calibrated (macro model prior)",
        "inv_confidence_assumption_grade": "Assumption-grade (best guess, not yet tested)",
        "inv_confidence_blocked": "Blocked (never funded)",
        "inv_mmm_heading": "Macro channel calibration (MMM)",
        "inv_mmm_available": "Macro calibration supplied — channel-level contribution below.",
        "inv_mmm_deferred": "Live PyMC-Marketing fitting is deferred to a later phase — this cycle used no macro model.",
        "inv_mmm_missing": "No macro calibration was supplied this cycle — every ROI number above is HTE-only, not MMM-blended.",
        "inv_qini_missing": "No holdout validation (Qini/AUUC) was supplied — do not read the ROI numbers above as causally proven; they are the model's best estimate, not yet tested against a random holdout.",
    },
    "zh": {
        "ch1_title": "1 · 拍板",
        "ch1_question": "这钱到底花不花？",
        "ch2_title": "2 · 这笔账",
        "ch2_question": "为什么？账是怎么算出来的？",
        "ch3_title": "3 · 打法",
        "ch3_question": "对谁打、在哪打、说什么？",
        "ch4_title": "4 · 执行",
        "ch4_question": "谁去做、什么时候、花多少钱——怎么算赢？",
        "ch5_title": "5 · 底牌",
        "ch5_question": "凭什么信这份报告？哪里可能翻车？",
        "ch_answer_label": "一句话回答",
        "ans_verdict_go": "花——但按第 4 章的放行条件分批放钱。",
        "ans_verdict_nogo": "不花——账算不过来，别投广告。",
        "ans_verdict_conditional": "先不花——把零成本的事做完，到检查点再拍板。",
        "ans_money": "卖一件赚 {margin}，所以拉来一个买家最多花 {ceiling}——{counts}。",
        "ans_money_counts": "{viable} 条渠道确定能赚、{undetermined} 条看不清、{notviable} 条必亏",
        "ans_play": "{channels} 条渠道值得试；主攻人群：{dims}；{suppress} 类人绝对不碰。",
        "ans_execution": "{cards} 张任务卡，{blocked} 张冻结中等数据落地；每张卡都带止损线。",
        "ans_receipts": "{sourced} 个数查证过（带链接）、{assumed} 个是假设（依据写明）、{missing} 个还没拿到——最薄弱的点：{weakest}",
        "verdict_word_viable": "能赚 (viable)",
        "verdict_word_not-viable": "必亏 (not-viable)",
        "verdict_word_undetermined": "看不清——先拿数 (undetermined)",
        "verdict_word_role-only": "只当辅助 (role-only)",
        "verdict_big_go": "干——可以花钱",
        "verdict_big_no-go": "不干——别花钱",
        "verdict_big_conditional": "先等等——查完再拍板",
        "grade_H": "主攻",
        "grade_T": "测试",
        "grade_S": "小注",
        "grade_N": "不投",
        "grade_A": "别碰",
        "cac_ceiling_word": "获客成本红线 (CAC ceiling)",
        "unit_margin_word": "卖一件赚的钱",
        "kill_line_word": "止损线",
        "blocked_word": "冻结——以下事项落实前不批钱：",
        "gate_word": "放行条件",
        "owner_word": "负责人",
        "due_word": "截止",
        "success_word": "成功线",
        "never_do_heading": "绝对不做（此测算下）",
        "prov_legend": "每个数字的来路：◆ 查证过（附链接）· ◇ 假设（依据写明）· ⊕ 算出来的（过程可见）· ○ 还没拿到（绝不编数）",
        "cac_caption": "看图：柱子伸过红线＝亏钱 · 完全在红线内＝赚钱 · 横跨红线＝看不清、先拿数。本图：{viable} 条能赚、{undetermined} 条看不清、{notviable} 条必亏。",
        "heatmap_caption": "看图：主攻＝钱先花在这 · 别碰＝对这些人投放是烧钱（他们会买便宜款，或者不投也会买）。",
        "task_cards_heading": "任务卡（一张卡＝一件有人负责的事）",
        "other_tests_heading": "独立试验（未挂到任务卡）",
        "test_in_card_label": "试验与止损",
        "why_now_label": "为什么是现在",
        "toc_title": "五个问题",
        "cat_ans_ch1": "共 {total} 个 SKU：{grow} 个加大投入、{hold} 个维持、{harvest} 个收割、{exit} 个退出。",
        "cat_ans_ch2": "{total} 条诊断发现——{critical} 条严重、{major} 条重要、{watch} 条观察（严重度已按证据等级封顶）。",
        "cat_ans_ch3": "覆盖 {tiers} 个价格带、{skus} 个 SKU 的定位与竞对地图。",
        "cat_ans_ch4": "{n} 个 SKU 判定加大投入（{skus}）——确认后送入单品分析流程。",
        "cat_ans_ch1_invest": " 投资：投 {spend} {currency}，换 {units} 件增量销量、{profit} {currency} 增量毛利（ROI {roi}x）；{never} 个格子这轮没批钱。",
        "cat_ans_ch2_invest": " 上面这笔钱是按边际回报从高到低排出来的，花到 {lambda_star}x 这道这轮最低达标线为止——具体曲线见下方。",
        "cat_ans_ch3_invest": " 具体到打法上，这轮有 {n_cells} 个 SKU × 打法模块的组合拿到了预算——具体分布见下方矩阵。",
        "cat_ans_ch4_invest": " 这轮共批出 {n_cells} 个 SKU × 打法模块的落地动作（见下方任务卡）；另有 {never} 个格子还需要更多证据才能批钱。",
        "cat_ans_ch5_invest": " 拿到钱的部分里，{validated} 个格子有验证过的试验撑腰、{mmm_calibrated} 个靠 MMM 校准、{assumption_grade} 个还是假设级。{mmm_note}",
        "inv_ch1_heading": "预算花在哪",
        "inv_kpi_spend": "建议投入",
        "inv_kpi_units": "增量销量",
        "inv_kpi_gross_profit": "增量毛利",
        "inv_kpi_net_profit": "净利润",
        "inv_kpi_roi": "投产比 (ROI)",
        "inv_kpi_lambda_star": "止投线 (λ*)",
        "inv_never_funded_heading": "这轮没批钱的",
        "inv_never_funded_empty": "所有符合条件的格子都批到钱了。",
        "inv_reason_excluded_verdict": "SKU 判定为收割/退出，规则上排除",
        "inv_reason_confidence_blocked": "证据不够（tau_source 缺失或测量条件未就绪）",
        "inv_th_sku": "SKU",
        "inv_th_module": "打法模块",
        "inv_th_reason": "为何冻结",
        "inv_frontier_heading": "钱越花越多，账怎么变（预算曲线）",
        "inv_frontier_profit_title": "投入越多，累计毛利怎么涨",
        "inv_frontier_roi_title": "边际投产比——每多花一份钱，值不值",
        "inv_frontier_caption": "看图：沿右图从左往右看，虚线是边际 ROI 跌破达标线的位置；就算预算还有富余，过了这条线也不再批钱。",
        "inv_matrix_heading": "钱落在哪：SKU × 打法模块",
        "inv_matrix_caption": "看图：格子越深＝花的钱越多；圆点颜色＝证据等级——绿＝验证过、蓝＝MMM 校准、黄＝假设级。",
        "inv_matrix_empty": "没有一格过了投产比门槛。",
        "inv_th_spend": "投入",
        "inv_th_roi": "投产比",
        "inv_tasks_heading": "落地任务卡（这轮批到钱的动作）",
        "inv_th_confidence": "证据等级",
        "inv_confidence_heading": "这笔预算有多少是站得住脚的证据",
        "inv_confidence_validated": "验证过（随机试验 + 有测量条件）",
        "inv_confidence_mmm_calibrated": "MMM 校准（宏观模型先验）",
        "inv_confidence_assumption_grade": "假设级（最佳猜测，还没测）",
        "inv_confidence_blocked": "冻结（没批钱）",
        "inv_mmm_heading": "宏观渠道校准（MMM）",
        "inv_mmm_available": "已提供宏观校准——渠道级贡献见下。",
        "inv_mmm_deferred": "实时 PyMC-Marketing 拟合推迟到后续阶段——这轮没有用宏观模型。",
        "inv_mmm_missing": "这轮没有提供宏观校准——上面所有 ROI 都只是 HTE 口径，没有和 MMM 融合。",
        "inv_qini_missing": "没有提供 holdout 验证（Qini/AUUC）——上面的 ROI 数字不能当作因果已证实，只是模型的最佳估计，还没有拿随机 holdout 测过。",
    },
}


# ── Lookup ────────────────────────────────────────────────────────────────────

def lang_of(cfg: dict) -> str:
    lang = str(cfg.get("meta", {}).get("lang", "en")).lower()
    return "zh" if lang.startswith("zh") else "en"


def lookup(cfg: dict, key: str, default: str) -> str:
    """labels override > operator pack (meta.lang) > zh legacy base > call-site default."""
    labels = cfg.get("labels", {})
    if key in labels:
        return labels[key]
    lang = lang_of(cfg)
    pack = OPERATOR_STRINGS.get(lang, {})
    if key in pack:
        return pack[key]
    if lang == "zh" and key in ZH_BASE:
        return ZH_BASE[key]
    return default


def S(cfg: dict, key: str) -> str:
    """Strict operator-string lookup: key must exist in OPERATOR_STRINGS."""
    labels = cfg.get("labels", {})
    if key in labels:
        return labels[key]
    return OPERATOR_STRINGS[lang_of(cfg)].get(key, OPERATOR_STRINGS["en"][key])


def grade_label(cfg: dict, code: str) -> str:
    """H/T/S/N/A -> operator word; unknown codes pass through."""
    return S(cfg, f"grade_{code}") if f"grade_{code}" in OPERATOR_STRINGS["en"] else code


def verdict_word(cfg: dict, code: str) -> str:
    key = f"verdict_word_{code}"
    return S(cfg, key) if key in OPERATOR_STRINGS["en"] else code


# ── Task-card merge: actions + test_plan + priority_plays -> one card each ───

def merge_task_cards(cfg: dict) -> dict[str, Any]:
    """Unify the three arrays that describe the same moves.

    Association is explicit: a test_plan row or priority_play row may carry
    "card": "<action id>". Rows without it stay stand-alone (backward compat).
    Returns {"cards": [...], "loose_tests": [...], "loose_plays": [...]}.
    Card order: plays' order first (they are the priority ranking), then the
    remaining actions in config order.
    """
    cards: dict[str, dict] = {}
    for i, a in enumerate(cfg.get("actions", []), 1):
        aid = a.get("id") or f"A{i}"
        card = dict(a)
        card["id"] = aid
        card["tests"] = []
        card["play"] = None
        cards[aid] = card

    loose_tests = []
    for t in cfg.get("test_plan", []):
        aid = t.get("card")
        if aid and aid in cards:
            cards[aid]["tests"].append(t)
        else:
            loose_tests.append(t)

    loose_plays = []
    ranked: list[str] = []
    for p in cfg.get("priority_plays", []):
        aid = p.get("card")
        if aid and aid in cards:
            cards[aid]["play"] = p
            ranked.append(aid)
        else:
            loose_plays.append(p)

    ordered = [cards[a] for a in ranked]
    ordered += [c for aid, c in cards.items() if aid not in ranked]
    return {"cards": ordered, "loose_tests": loose_tests, "loose_plays": loose_plays}


# ── Auto-generated chapter answers (config can override via cfg["chapter_answers"]) ──

def _is_range(v) -> bool:
    return isinstance(v, list) and len(v) == 2


def _fmt_money(spec: dict) -> str:
    v = spec.get("value")
    unit = spec.get("unit", "")
    if v is None:
        return "—"
    if _is_range(v):
        return f"{v[0]:,.10g}–{v[1]:,.10g} {unit}".strip()
    return f"{v:,.10g} {unit}".strip()


def _screen_counts(cfg: dict) -> dict[str, int]:
    counts = {"viable": 0, "not-viable": 0, "undetermined": 0, "role-only": 0}
    for ch in cfg.get("channel_screen", []):
        v = ch.get("verdict", "undetermined")
        counts[v] = counts.get(v, 0) + 1
    return counts


def chapter_answers(cfg: dict, numbers: dict) -> dict[str, str]:
    """One plain-language line per chapter, computed from the data.
    cfg["chapter_answers"][chX] overrides any of them."""
    overrides = cfg.get("chapter_answers", {})
    memo = cfg.get("decision_memo", {})
    verdict = memo.get("verdict", "conditional")

    out: dict[str, str] = {}

    key = {"go": "ans_verdict_go", "no-go": "ans_verdict_nogo"}.get(verdict, "ans_verdict_conditional")
    out["ch1"] = S(cfg, key)

    margin_id = next((n for n in ("unit_margin",) if n in numbers), None)
    ceiling_id = cfg.get("cac_chart", {}).get("ceiling_id", "cac_ceiling")
    counts = _screen_counts(cfg)
    counts_txt = S(cfg, "ans_money_counts").format(
        viable=counts["viable"], undetermined=counts["undetermined"], notviable=counts["not-viable"])
    out["ch2"] = S(cfg, "ans_money").format(
        margin=_fmt_money(numbers.get(margin_id, {})) if margin_id else "—",
        ceiling=_fmt_money(numbers.get(ceiling_id, {})) if ceiling_id in numbers else "—",
        counts=counts_txt)

    dims = [d.get("name", d.get("id", "")) for d in cfg.get("dimensions", [])
            if str(d.get("verdict", "")).lower().startswith("retain")]
    testable = counts["viable"] + counts["undetermined"]
    out["ch3"] = S(cfg, "ans_play").format(
        channels=testable, dims="、".join(dims[:3]) if lang_of(cfg) == "zh" else ", ".join(dims[:3]) or "—",
        suppress=len(cfg.get("suppression_rules", [])))

    merged = merge_task_cards(cfg)
    challenges_by_id = {c.get("id"): c for c in cfg.get("challenges", [])}
    blocked = sum(1 for c in merged["cards"]
                  if any(challenges_by_id.get(b, {}).get("status") == "open-blocking"
                         for b in c.get("blocked_by", [])))
    out["ch4"] = S(cfg, "ans_execution").format(cards=len(merged["cards"]), blocked=blocked)

    prov = {"sourced": 0, "assumed": 0, "derived": 0, "missing": 0}
    for spec in numbers.values():
        prov[spec.get("provenance", "missing")] = prov.get(spec.get("provenance", "missing"), 0) + 1
    out["ch5"] = S(cfg, "ans_receipts").format(
        sourced=prov["sourced"], assumed=prov["assumed"], missing=prov["missing"],
        weakest=memo.get("weakest_point", "—"))

    out.update({k: v for k, v in overrides.items() if k in CHAPTER_IDS})
    return out


def cac_caption(cfg: dict, bars: list) -> str:
    """Auto 'how to read' line for the CAC chart. bars = [(name, lo, hi, verdict)]."""
    counts = {"viable": 0, "not-viable": 0, "undetermined": 0}
    for _, _, _, v in bars:
        counts[v] = counts.get(v, 0) + 1
    return S(cfg, "cac_caption").format(
        viable=counts["viable"], undetermined=counts["undetermined"],
        notviable=counts["not-viable"])


# ── Severity-capping (shared by generate_report.py's category diagnosis
#    renderer and category_chapter_answers below — a claim on thin evidence
#    is downgraded to the highest severity its proof can carry) ──────────────

GRADE_RANK = {"sourced": 2, "derived": 2, "assumed": 1, "hypothesis": 0, "missing": 0}
SEV_NEED = {"critical": 2, "major": 1, "watch": 0}


def cap_severity(sev: str, grade: str) -> tuple[str, bool]:
    g = GRADE_RANK.get((grade or "").lower(), 0)
    if SEV_NEED.get(sev, 0) <= g:
        return sev, False
    for cand in ("critical", "major", "watch"):
        if SEV_NEED[cand] <= g:
            return cand, True
    return "watch", True


# ── Category-portfolio chapter answers (parallel to chapter_answers() above,
#    but for report_type=category_portfolio configs, which have no
#    decision_memo/channel_screen — the counts come from portfolio/diagnosis) ──

CATEGORY_ANSWER_KEYS = [
    "cat_ans_ch1", "cat_ans_ch2", "cat_ans_ch3", "cat_ans_ch4", "cat_ans_ch5",
]


def category_chapter_answers(cfg: dict, numbers: dict) -> dict[str, str]:
    overrides = cfg.get("chapter_answers", {})
    portfolio = cfg.get("portfolio", [])
    diagnosis = cfg.get("diagnosis", [])
    lang = lang_of(cfg)
    sep = "、" if lang == "zh" else ", "

    counts = {"grow": 0, "hold": 0, "harvest": 0, "exit": 0}
    for p in portfolio:
        v = p.get("verdict", "hold")
        counts[v] = counts.get(v, 0) + 1
    out = {"ch1": S(cfg, "cat_ans_ch1").format(
        total=len(portfolio), grow=counts["grow"], hold=counts["hold"],
        harvest=counts["harvest"], exit=counts["exit"])}

    sev_counts = {"critical": 0, "major": 0, "watch": 0}
    for d in diagnosis:
        sev, _ = cap_severity(d.get("severity", "watch"), d.get("evidence_grade", "hypothesis"))
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
    out["ch2"] = S(cfg, "cat_ans_ch2").format(
        total=len(diagnosis), critical=sev_counts["critical"],
        major=sev_counts["major"], watch=sev_counts["watch"])

    tiers = cfg.get("price_tiers", [])
    out["ch3"] = S(cfg, "cat_ans_ch3").format(tiers=len(tiers), skus=len(portfolio))

    grow_skus = [p.get("sku", "") for p in portfolio if p.get("verdict") == "grow"]
    out["ch4"] = S(cfg, "cat_ans_ch4").format(
        n=len(grow_skus), skus=sep.join(grow_skus[:3]) or "—")

    prov = {"sourced": 0, "assumed": 0, "derived": 0, "missing": 0}
    for spec in numbers.values():
        prov[spec.get("provenance", "missing")] = prov.get(spec.get("provenance", "missing"), 0) + 1
    out["ch5"] = S(cfg, "ans_receipts").format(
        sourced=prov["sourced"], assumed=prov["assumed"], missing=prov["missing"],
        weakest=cfg.get("_note", "—"))

    out.update({k: v for k, v in overrides.items() if k in CHAPTER_IDS})
    return out


def investment_chapter_answers(cfg: dict, inv: dict) -> dict[str, str]:
    """One overlay sentence per chapter when cfg["investment_plan"] is
    present, appended to that chapter's base one-line answer. Each chapter
    now also carries an investment section (KPIs+never-funded in ch1, the
    frontier chart in ch2, the budget matrix in ch3, activation cards in
    ch4, confidence+MMM in ch5) — the banner must say so, not just the
    portfolio-diagnosis story the chapter answered before this capability
    existed."""
    answer = inv.get("answer", {})
    blocked = inv.get("blocked", [])
    confidence = inv.get("charts", {}).get("confidence", {})
    mmm = inv.get("mmm", {})
    n_cells = len(answer.get("allocation", []))

    out = {
        "ch1": S(cfg, "cat_ans_ch1_invest").format(
            spend=f'{answer.get("recommended_spend", 0.0):,.0f}',
            currency=inv.get("currency", ""),
            units=f'{answer.get("incremental_units", 0.0):,.0f}',
            profit=f'{answer.get("incremental_gross_profit", 0.0):,.0f}',
            roi=round(answer.get("roi", 0.0), 2),
            never=len(blocked)),
        "ch2": S(cfg, "cat_ans_ch2_invest").format(
            lambda_star=round(answer.get("lambda_star", 0.0), 2)),
        "ch3": S(cfg, "cat_ans_ch3_invest").format(n_cells=n_cells),
        "ch4": S(cfg, "cat_ans_ch4_invest").format(n_cells=n_cells, never=len(blocked)),
        "ch5": S(cfg, "cat_ans_ch5_invest").format(
            validated=confidence.get("validated", 0),
            mmm_calibrated=confidence.get("mmm_calibrated", 0),
            assumption_grade=confidence.get("assumption_grade", 0),
            mmm_note=S(cfg, f'inv_mmm_{mmm.get("status", "missing")}')),
    }
    return out


# ── Legacy Chinese label base (extracted from the zh sample config so zh
#    configs no longer need to ship ~340 labels; any key can still be
#    overridden per-config via cfg["labels"]) ─────────────────────────────────

ZH_BASE: dict[str, str] = {
    "actions_heading": "附 · Treatment Cards 汇总",
    "actions_intro": "仅通过可行性筛查的选项以卡片形式出现。标有 <strong>⊘ BLOCKED</strong> 的卡片引用了未解决的阻塞性挑战（第4节），必须在解决该挑战之前不得分配预算。",
    "actions_rejected_heading": "已拒绝选项（及原因）",
    "actions_rejected_th_option": "选项",
    "actions_rejected_th_reason": "拒绝原因",
    "assumption_register_heading": "假设登记表",
    "bg_th_budget": "预算",
    "bg_th_condition": "解锁条件",
    "bg_th_item": "项目",
    "bg_th_phase": "阶段",
    "budget_chart_title": "预算分配概览",
    "budget_envelope_label": "预算额度",
    "budget_heading": "10 · 预算分配",
    "budget_th_budget": "预算",
    "budget_th_condition": "条件",
    "budget_th_item": "项目",
    "budget_th_phase": "阶段",
    "cac_chart_caption": "横条=基准 CAC 区间 · 竖线=上限 · 颜色=筛查结论。基准只能证伪（最优情况超上限即出局），无法证明可行——所以即便整条在上限左侧，未经本地数据确认前仍为「待定」。",
    "cac_chart_ceiling_label": "CAC 上限",
    "cac_chart_title": "各渠道 CAC 区间 vs 上限（CZK）",
    "cac_legend_notviable": "不可行（最优情况仍超上限）",
    "cac_legend_undetermined": "待定（基准估算，无法据此判定可行）",
    "cac_legend_viable": "可行（本地数据确认低于上限）",
    "card_audience": "受众",
    "card_baseline": "基线",
    "card_decision_date": "决策日期",
    "card_guardrail": "护栏",
    "card_kill_line": "止损线",
    "card_measurement": "测量",
    "card_mechanism": "机制",
    "card_prediction": "预测",
    "card_test": "测试",
    "card_unlocks": "解锁条件",
    "ch_th_challenge": "挑战",
    "ch_th_question": "问题",
    "ch_th_resolution": "解决 / 所需证据",
    "ch_th_status": "状态",
    "challenges_heading": "9 · 因果激活评审（campaign 级）",
    "challenges_intro": "挑战由独立评审过程提出，不可更改——分析方可回应但不得改写。<strong>open-blocking</strong> 挑战为每个依赖它的行动打上标记。公开展示未解决的挑战是信任机制；\"resolved\" 需要数据，而非说辞。",
    "challenges_th_challenge": "挑战",
    "challenges_th_question": "问题",
    "challenges_th_resolution": "解决方案 / 所需证据",
    "challenges_th_status": "状态",
    "channel_benchmark_note": "基准可以证明<em>不可行</em>（最优情况仍超上限），但<em>无法</em>证明可行。<em>undetermined</em> = 区间横跨上限；需要获取数据。",
    "channel_heading": "4 · 本地渠道地图",
    "channel_note": "基准可以证明<em>不可行</em>（最优情况仍超上限），但<em>无法</em>证明可行。<em>undetermined</em> = 区间横跨上限；需要获取数据。",
    "channel_th_cac": "CAC 估算",
    "channel_th_name": "渠道",
    "channel_th_note": "备注",
    "channel_th_proxy": "Proxy 质量",
    "channel_th_task": "任务",
    "channel_th_verdict": "结论",
    "chart_cate_bimodal": "双峰——两类人",
    "chart_cate_spike": "尖峰——无异质性（别个性化）",
    "chart_cate_wide": "宽分布——值得分层",
    "chart_cate_x": "预测 uplift  τ(x)  →",
    "chart_cate_y": "用户数",
    "chart_cate_zero": "τ = 0",
    "chart_f_against": "←  压低 τ",
    "chart_f_anxiety": "Anxiety · 换新的恐惧",
    "chart_f_habit": "Habit · 习惯惯性",
    "chart_f_pull": "Pull · 产品吸引力",
    "chart_f_push": "Push · 对现状不满",
    "chart_f_toward": "抬高 τ  →",
    "chart_q_lost": "无望者\n浪费预算",
    "chart_q_no": "否",
    "chart_q_persona": "高 Push + 高 Anxiety",
    "chart_q_persuadable": "可说服者\n✓ 投这些人",
    "chart_q_sleeping": "沉睡狗\n投了反而跑",
    "chart_q_sure": "铁定会买\n浪费预算",
    "chart_q_x": "不投放也会买",
    "chart_q_y": "投放后会买",
    "chart_q_yes": "是",
    "chart_qini_band": "行业基准（Qini ≈ 0.25–0.40）",
    "chart_qini_perfect": "完美模型（上界）",
    "chart_qini_random": "随机投放",
    "chart_qini_x": "触达人群比例（按预测 uplift 排序）",
    "chart_qini_y": "累计增量转化（%）",
    "chart_wf_attributed": "平台归因",
    "chart_wf_axis": "收入（示意单位）",
    "chart_wf_incremental": "真实增量",
    "chart_wf_organic": "− 自然 / 季节",
    "chart_wf_sure": "− 本来就会买",
    "checklist_heading": "17 · 来源与核验清单",
    "cm_th_cac": "CAC 估算",
    "cm_th_channel": "渠道",
    "cm_th_note": "备注",
    "cm_th_proxy": "Proxy 质量",
    "cm_th_task": "任务",
    "cm_th_verdict": "结论",
    "decision_date_label": "决策日期",
    "depth_deep_banner": "完整报告 + 汇总的验证路线图（§18）——所有未决假设按「能否改变决策」排序。",
    "depth_label_deep": "深度",
    "depth_label_quick": "速览",
    "depth_quick_banner": "仅保留决策关键章节——总结、备忘、单位经济、门控与证据。去掉 --depth quick 可查看完整分析。",
    "dim_chart_title": "D 维度评分排名",
    "dim_heading": "5 · D 维度表与因果激活评审",
    "dim_reviewer_callout": "D 维度是试验设计的候选操作变量。在进入主要预算之前，每个维度必须通过：可部署的 Proxy、可测试的增量效果、已陈述的机制、无合规或边际风险。",
    "dim_reviewer_heading": "因果激活评审 — 维度挑战",
    "dim_reviewer_th_challenge": "提出的挑战",
    "dim_reviewer_th_dimension": "维度",
    "dim_reviewer_th_evidence": "所需证据",
    "dim_reviewer_th_handling": "当前处理",
    "dim_th_id": "维度",
    "dim_th_mechanism": "机制",
    "dim_th_proxy": "平台 Proxy",
    "dim_th_score": "评分",
    "dim_th_status": "状态",
    "dim_th_verdict": "评审结论",
    "dim_verdict_legend": "结论说明：Retain = 热力图 H 或 T · Retain (test) = T 或 S · Demote S = 仅 S · Suppression = 抑制目标 · Delete = 剔除。",
    "dt_th_dimension": "维度",
    "dt_th_mechanism": "机制",
    "dt_th_proxy": "平台 Proxy",
    "dt_th_score": "评分",
    "dt_th_status": "状态",
    "dt_th_verdict": "判定",
    "ec_cate_badge": "示意图",
    "ec_cate_sub": "单一尖峰=人人反应一样，别个性化；宽分布或双峰=uplift 存在异质性，分层投放才划算。",
    "ec_cate_title": "到底该不该个性化？看 τ(x) 的分布形状",
    "ec_forces_badge": "机制图",
    "ec_forces_sub": "Push 与 Pull 推向购买；Habit 与 Anxiety 拉住不买。只有当 treatment 移动了一个仍未定的力，才会产生增量。",
    "ec_forces_title": "treatment 必须撬动什么：四种力",
    "ec_qini_badge": "示意（待填）",
    "ec_qini_reb": "若实测 Qini < 0.15，曲线贴回随机线——说明特征无 uplift 信号，应放弃个性化，改用统一策略。",
    "ec_qini_sub": "模型曲线与随机线之间的面积，就是模型创造的价值。色带是电商行业基准区间；你的曲线需在 holdout 数据上运行 qini_auuc.py 填入。",
    "ec_qini_title": "模型是否胜过随机投放？（Qini 曲线）",
    "ec_quad_badge": "概念图",
    "ec_quad_sub": "按购买概率投放，命中的是「铁定会买」；按 uplift 投放，才找得到「可说服者」——唯一因你的动作才购买的人。",
    "ec_quad_title": "谁值得投放：四种响应类型",
    "ec_wf_badge": "示意",
    "ec_wf_reb": "比例为示意；真实拆分需 holdout。若 holdout 增量与平台归因差距 < 5%，则此拆分不成立，归因可直接采信。",
    "ec_wf_sub": "平台归因把碰过的每笔转化都算作自己的功劳。剔除本来就会买的人，再剔除自然与季节性需求，剩下的才是花费真正带来的。",
    "ec_wf_title": "从归因收入到真实增量",
    "echart_fallback": "交互图表需加载 ECharts（联网获取）。断网时请联网后刷新查看。",
    "echart_reb_label": "推翻条件",
    "eg_heading": "8 · 执行门禁与 Treatment Cards",
    "eg_maturity_note": "本分析支持试验设计与渠道筛查，不支持 CATE 断言或策略优化。",
    "eg_tcards_heading": "Treatment Cards（仅 H-main 单元）",
    "eg_th_gate": "门禁",
    "eg_th_input": "所需输入",
    "eg_th_note": "备注",
    "eg_th_status": "状态",
    "ev_th_accessed": "访问日期",
    "ev_th_assumption": "假设",
    "ev_th_basis": "依据",
    "ev_th_blocks": "阻塞",
    "ev_th_cost": "成本",
    "ev_th_fact": "事实",
    "ev_th_source": "来源",
    "ev_th_value": "值",
    "ev_th_what": "内容",
    "ev_th_where": "从何获取",
    "evidence_assumed_heading": "假设登记",
    "evidence_heading": "16 · 证据与缺口",
    "evidence_missing_heading": "缺失台账 — 按敏感性排序，即工作计划",
    "evidence_sourced_heading": "已溯源事实",
    "evidence_th_accessed": "访问日期",
    "evidence_th_assumption": "假设",
    "evidence_th_basis": "依据",
    "evidence_th_blocks": "阻塞",
    "evidence_th_cost": "成本",
    "evidence_th_fact": "事实",
    "evidence_th_missing": "缺失项",
    "evidence_th_source": "来源",
    "evidence_th_value": "值",
    "evidence_th_where": "获取渠道",
    "footer_method": "方法论",
    "footer_note": "每个数字均为溯源、假设、推导或缺失——无任何数字是凭空捏造的",
    "gates_cards_heading": "Treatment Cards（仅 H 主投格）",
    "gates_heading": "9 · 执行门与 Treatment Cards",
    "gates_maturity_prefix": "成熟度：",
    "gates_maturity_suffix": " — 本分析支持试验设计和渠道筛查，不支持 CATE 声明或策略优化。",
    "gates_th_gate": "执行门",
    "gates_th_input": "所需输入",
    "gates_th_note": "备注",
    "gates_th_status": "状态",
    "guardrail_label": "护栏",
    "heatmap_corner": "渠道 / 维度",
    "heatmap_heading": "6 · 语义热力图（渠道 × 维度）",
    "heatmap_intro": "仅通过可行性筛查的渠道出现在此。H = 主要投资目标；A = 主动抑制。",
    "heatmap_legend_label": "图例",
    "heatmap_legend_prefix": "图例：",
    "hmain_heading": "7 · H-Main 拆解",
    "hmain_intro": "以下是预期 HTE 为正的单元。每个对应执行门禁节中的一张 Treatment Card。优先级自上而下。",
    "hmain_th_card": "Treatment Card",
    "hmain_th_cell": "渠道 × 维度",
    "hmain_th_hypothesis": "HTE 假设",
    "hmain_th_notes": "备注",
    "hmain_th_tcard": "Treatment Card",
    "horizon_checkpoint": "检查点时",
    "horizon_never": "此测算下不做",
    "horizon_now": "现在（零成本）",
    "kill_line_label": "止损线",
    "kol_attribution": "归因",
    "kol_fee": "费用估算",
    "kol_fee_pending": "待直接报价",
    "kol_fee_suffix": "待直接询价",
    "kol_format": "形式",
    "kol_heading": "12 · KOL / 达人采购",
    "kol_incrementality": "增量性",
    "ledger_heading": "18 · 验证路线图",
    "ledger_intro": "按（是否阻塞 × 验证成本）排序：open-blocking 挑战与阻塞预算的缺口在前，仅影响敏感性的输入在后。每行都带一条预先承诺的判定线——假设只有在其测试通过后才能晋升为 Sourced。",
    "lg_blocks_prefix": "阻塞：",
    "lg_by": "截止",
    "lg_empty": "无未决假设、无缺失输入、无待测项——没有需要验证的内容。",
    "lg_prov_hypothesis": "Hypothesis",
    "lg_prov_missing": "Missing",
    "lg_risk_blocking": "阻塞依赖它的动作",
    "lg_risk_kill": "预测不成立则该动作被砍",
    "lg_risk_open": "未决挑战——暂未阻塞",
    "lg_risk_sens": "敏感性输入——不阻塞任何动作",
    "lg_rule_challenge": "挑战澄清 → 动作解锁；否则保持 BLOCKED",
    "lg_rule_missing": "拿到该值 → 晋升为 Sourced / Assumed",
    "lg_th_assumption": "假设 / 未决问题",
    "lg_th_prov": "当前来源等级",
    "lg_th_rank": "#",
    "lg_th_risk": "若错了",
    "lg_th_rule": "通过 / 否决规则",
    "lg_th_test": "最小有效验证",
    "marker_legend": "数字标记：◆S 已溯源（带链接）· ◇A 假设（已述依据）· ⊕D 推导（展示链条）· ○M 缺失（无值，仅占位）",
    "market_facts_heading": "市场事实",
    "market_th_fact": "事实",
    "market_th_status": "状态",
    "math_heading": "2 · 测算",
    "maturity_label": "成熟度",
    "measurement_gcg": "全局对照组（GCG）设计",
    "measurement_heading": "13 · 测量计划",
    "measurement_pause": "暂停规则",
    "measurement_primary": "主指标",
    "measurement_scaleup": "放量规则",
    "measurement_secondary": "次要指标",
    "mechanism_label": "机制",
    "memo_heading": "1 · 决策备忘",
    "mf_th_fact": "事实",
    "mf_th_status": "状态",
    "missing_ledger_heading": "缺失账本 — 按敏感性排序，这就是工作计划",
    "ml_l0": "L0 — 实验前",
    "ml_l0_desc": "尚未设置 holdout",
    "ml_l1": "L1 — GCG + 回溯分析",
    "ml_l1_desc": "随机 holdout 对照",
    "ml_l2": "L2 — 策略学习 + OPE",
    "ml_l2_desc": "离线验证",
    "ml_l3": "L3 — 上下文 Bandit",
    "ml_l3_desc": "在线学习",
    "mp_gcg": "GCG 设计",
    "mp_pause": "暂停规则",
    "mp_primary": "主指标：",
    "mp_scaleup": "扩量规则",
    "mp_secondary": "次级指标：",
    "overturn_heading": "什么会推翻这个论点",
    "pf_th_feature": "功能",
    "pf_th_relevance": "定向相关性",
    "pf_th_status": "状态",
    "plays_expected_cac": "预期增量 CAC",
    "plays_heading": "11 · 优先打法与 ROI 情景",
    "plays_kill_line": "止损线",
    "plays_why_now": "为何现在",
    "pp_expected_cac": "预期增量 CAC",
    "pp_kill_line": "止损线",
    "pp_why_now": "为何现在",
    "prediction_label": "预测",
    "price_comparison_title": "竞品价格定位",
    "product_features_heading": "与定向相关的产品功能",
    "product_heading": "3 · 产品与市场事实",
    "product_th_feature": "功能",
    "product_th_relevance": "定向相关性",
    "product_th_status": "状态",
    "rejected_heading": "被否决的选项（及原因）",
    "rejected_th_option": "选项",
    "rejected_th_reason": "否决原因",
    "reviewer_callout": "D 维度是试验设计的候选操作变量。进入主预算前，每个维度都须通过：可部署 Proxy、可测增量、有明确机制、无合规或利润风险。",
    "reviewer_heading": "因果激活评审 — 维度挑战",
    "rv_th_challenge": "提出的挑战",
    "rv_th_dimension": "维度",
    "rv_th_evidence": "所需证据",
    "rv_th_handling": "当前处理",
    "s10_intro": "预算分配遵循渠道筛查和执行门控——而非相反。只有通过筛查的渠道才能获得资金。每一行均以第 8 节中某个门控条件被满足为前提。预算不会在假设中移动——它在完成执行门控后才真正移动。",
    "s11_intro": "综合渠道筛查、维度评分和预算结构，以下是未来 90 天预期回报最高的三个行动。每个策略对应其激活的干预卡，并附有终止线——一旦数据显示假设不成立，行动即停止。",
    "s12_intro": "达人资源整合遵循渠道地图：YouTube 和社交媒体承担内容资产角色，而非直接转化。达人内容产生认知并构建产品叙事——不能证明增量效果。在设置 holdout 对照组隔离因果效应之前，以下所有达人归因均标注为假设。",
    "s13_intro": "测量方案直接衔接第 5 节的 D 维度和第 8 节的干预卡。若没有此处指定的 GCG（随机对照设计），将无法区分营销造成的结果与趋势巧合。下方的成熟度阶梯显示当前项目所处位置及晋级所需条件。",
    "s14_intro": "第 8 节中的每张干预卡都附有可证伪的预测和终止线。这些不是里程碑——而是决策门。到决策日期，预测要么成为溯源证据，要么终止行动并回收预算。",
    "s15_intro": "屏蔽与定向同等重要。以下规则定义了不该触达的人群——保护利润、防范合规风险，避免将正向 CATE 策略变成负利润项目的逆向选择。",
    "s16_intro": "这是报告中每个数字的审计追踪记录。所有数值均为以下四种之一：已溯源（附链接）、已假设（明确陈述依据）、已推导（展示公式与输入）或缺失（占位符——无数值被发明）。",
    "s17_intro": "上线前核查清单。所有条目须达到「完成」状态，才能解锁任何预算。待处理条目阻断对应的干预卡。本清单是上方缺失台账的操作转化。",
    "s18_intro": "把整份报告里仍未证实、但决策依赖的东西汇成一张排序清单。它将未决评审挑战、缺失台账和测试预测合并为一条路线图，按「最便宜的阻塞项先测」排序。这里没有新东西——只是把报告其余部分按「什么能改变决策」重新排了序。",
    "s2_intro": "以上结论建立在一个核心经济逻辑上：单位毛利决定了客户获取成本（CAC）的上限。本报告中的每个渠道、每项行动，均以该上限为评判基准。基准估算只能证伪可行性——无法证实可行性。",
    "s3_intro": "经济模型划定了上限，本节将分析落地到产品现实：哪些功能具有差异化价值，产品如何在竞品中定位，哪些市场事实制约了渠道与受众策略。",
    "s4_intro": "CAC 上限已确立，现对每个渠道进行筛查：其获客成本区间能否低于上限？下方的结论标签给出快速答案，表格提供详细推理。请记住：基准只能排除渠道，不能确认渠道。",
    "s5_intro": "渠道筛查告诉我们在哪里触达买家。维度表则提出另一个问题：在这些渠道中，哪些买家特征能预测增量响应？每个维度在获得预算前须通过四项标准：可部署代理指标、可检验增量性、转化机制合理、监管合规。",
    "s6_intro": "热图将每个维度与每个渠道交叉比对。标记 H 的格子是主要投资目标——预期具有最强正向提升效果。标记 A 的格子需要主动屏蔽：向这些用户投放可能侵蚀利润，而非带来增长。",
    "s7_intro": "热图识别了所有 H 和 T 格子，本节聚焦 H-main 格子：预期具有正向增量提升的渠道-维度组合。每行直接对应第 8 节的一张干预卡。优先级从上至下排列。",
    "s8_intro": "干预卡将第 7 节的 H-main 假设转化为可操作的执行方案。每张卡明确触达对象（受众）、执行内容（机制）、风险保护（护栏）和测量方式（测试）。被阻断的卡意味着存在未解决的阻断性挑战，在挑战关闭前不得分配预算。",
    "s9_intro": "以下挑战由独立复核在初步分析完成后提出，属于不可篡改的记录——分析可以回应，但不能重写。阻断性未解决挑战会在所有依赖该挑战的行动上盖上 BLOCKED 标记。",
    "screen_heading": "渠道可行性筛查（阈值：上方 CAC 上限）",
    "screen_note": "规则：基准估算可以证明<em>不可行</em>（最优情况仍超上限），但<em>无法</em>证明可行——可行需要本地数据。<em>undetermined</em> 意味着区间横跨上限；行动是获取数据，而非选一个端点。",
    "screen_th_cac": "CAC 估算",
    "screen_th_channel": "渠道",
    "screen_th_reasoning": "原因 / 缺失数据",
    "screen_th_verdict": "结论",
    "sens_note": "按优先级顺序验证：P1 最先处理。",
    "sens_th_change": "假设变化",
    "sens_th_effect": "对结论的影响",
    "sens_th_priority": "验证优先级",
    "sensitivity_heading": "敏感性分析 — 哪个假设会翻转结论",
    "sourced_facts_heading": "已溯源事实",
    "sp_th_dimension": "维度",
    "sp_th_reason": "原因",
    "sp_th_rule": "规则",
    "suppression_heading": "15 · 抑制与风险规则",
    "suppression_th_dimension": "维度",
    "suppression_th_reason": "原因",
    "suppression_th_rule": "规则",
    "tag_assumption": "假设",
    "tag_needs_test": "待测试",
    "tc_audience": "受众",
    "tc_baseline": "基线",
    "tc_blocked_by": "被阻塞，来自",
    "tc_budget": "预算额度",
    "tc_guardrail": "护栏",
    "tc_measurement": "测量",
    "tc_mechanism": "机制",
    "termination_heading": "流程在第 {stage} 阶段终止",
    "termination_note": "本报告刻意保持简短：测算不支持媒体投放计划。能改变测算的杠杆已列在敏感性分析表和缺失账本中。其中之一发生变化时，重新运行流程。",
    "test_label": "测试",
    "testplan_heading": "14 · 测试计划",
    "testplan_intro": "每个进入预算的主张都带有可证伪的预测、止损线和决策日期。在该日期，该线要么成为已溯源数据，要么被宣告无效。",
    "thesis_label": "论点：",
    "tldr_do": "要做",
    "tldr_do_empty": "— 暂无 —",
    "tldr_dont": "不要做",
    "tldr_dont_empty": "— 暂无 —",
    "tldr_heading": "0 · 总结",
    "tldr_kicker": "一句话结论",
    "tldr_roi_cond": "未定——先完成零成本数据拉取再决定预算",
    "tldr_roi_label": "ROI",
    "tldr_why_label": "为什么",
    "toc_title": "目录",
    "unlocks_label": "解锁",
    "verdict_label": "裁决",
    "weakest_heading": "本报告最薄弱处",
}
