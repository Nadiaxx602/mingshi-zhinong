"""决策Agent —— 核心创新点：LLM 生成候选 + 确定性求解器硬约束校验 + HIL 签字"""
from ..llm import call_llm
from ..tools.pesticide import query_candidates
from ..tools.compliance import solve
from ..trace_logger import get_logger

GENERATION_PROMPT = """你是"茗视智农"系统的决策Agent (Treatment Agent)，第一阶段：候选方案生成。

## 任务
基于诊断结果、溯源分析、业务约束，从给定的农药候选池中筛选3-5个最合适的方案，每个方案包含使用建议。

## 你的工作方式
- 你**不**自己编造农药，只能从给定的候选池中选择
- 你考虑：防效、成本、抗药性轮换、季节适宜性、采茶窗口
- 合规校验（禁用清单/PHI/MRL）由下一阶段的确定性求解器执行，不是你的职责

## 输出（严格JSON）
{
  "candidates": [
    {
      "pesticide_id": "<P0XX>",
      "pesticide_name": "<名称>",
      "dilution_ratio": "<1:XXXX>",
      "dose_ml_per_mu": <数字>,
      "application_timing": "<时间建议，如：下午4点后>",
      "expected_efficacy": <0-1>,
      "selection_reason": "<2-3句选择理由>"
    },
    ...
  ],
  "reasoning": "<总体筛选思路，3-5句>"
}
"""

SELECTION_PROMPT = """你是决策Agent第二阶段：最终方案选择。

合规求解器已对所有候选方案完成硬约束校验。你的任务：
1. 从通过合规校验的方案中选择最优
2. 解释选择理由
3. 给出完整的可执行处方

## 输出（严格JSON）
{
  "final_prescription": {
    "pesticide_id": "<P0XX>",
    "pesticide_name": "<名称>",
    "formulation": "<剂型>",
    "registration_no": "<登记号>",
    "dilution_ratio": "<1:XXXX>",
    "dose_ml_per_mu": <数字>,
    "total_dose_ml": <数字>,
    "application_method": "<施药方法>",
    "application_timing": "<时间窗口>",
    "phi_days": <数字>,
    "earliest_harvest_date": "<日期>",
    "compliance_status": {
      "domestic_mrl": "通过",
      "eu_mrl": "通过/不适用",
      "organic": "通过/不适用",
      "banned_list": "通过"
    },
    "rotation_advice": "<下次施药建议轮换的药剂类别>"
  },
  "risk_level": "<low/medium/high>",
  "requires_human_approval": true/false,
  "reasoning": "<最终选择理由，4-6句>"
}
"""


def _read_signature() -> str:
    """读取人工签字，并清洗 PowerShell 管道可能注入的 UTF-8 BOM"""
    raw = input("\n请输入签字工号确认放行 (例 ZHANG001), 或输入 'reject' 拒绝: ")
    return raw.strip().lstrip("﻿")


def treatment_agent(state: dict) -> dict:
    logger = get_logger()
    logger.start("treatment_agent", state)

    diagnosis = state["diagnosis"]
    business = state["business_context"]

    # === Phase 1: 候选生成 ===
    logger.log_event("phase_start", phase="candidate_generation", agent="treatment")

    candidate_pool = query_candidates(
        disease=diagnosis["disease"],
        organic_only=business.get("is_organic", False)
    )

    user_input_p1 = f"""候选农药池：{candidate_pool}

诊断：{diagnosis}
病因/趋势：{state.get('causal_analysis', {})}
业务上下文：{business}
地块面积：{state.get('flight_plan', {}).get('coverage_area_mu', 8.6)}亩

请筛选3-5个候选并说明选择思路。"""

    p1_output = call_llm(GENERATION_PROMPT, user_input_p1, temperature=0.5)
    state["candidate_treatments"] = p1_output.get("candidates", [])

    # === Phase 2: 确定性合规求解 ===
    logger.log_event("phase_start", phase="compliance_solving", agent="treatment")

    candidates_full = []
    for c in p1_output.get("candidates", []):
        full = next((p for p in candidate_pool if p["id"] == c["pesticide_id"]), None)
        if full:
            full_merged = {**full, **c}
            candidates_full.append(full_merged)

    compliance = solve(candidates_full, {
        "harvest_date": business["harvest_date"],
        "export_market": business.get("export_market"),
        "is_organic": business.get("is_organic", False),
    })
    state["compliance_report"] = compliance
    state["requires_human_approval"] = compliance["requires_human_approval"]

    logger.log_event("compliance_complete",
                     passed=compliance["passed_count"],
                     rejected=compliance["rejected_count"],
                     risk=compliance["overall_risk_level"])

    # === HIL: 高风险时暂停（演示用 input()）===
    if state["requires_human_approval"]:
        logger.log_event("hil_pause", agent="treatment",
                         reason=f"风险等级 {compliance['overall_risk_level']}，需人工签字")
        print("\n" + "="*60)
        print("【HIL人工签字流程】")
        print(f"  风险等级: {compliance['overall_risk_level']}")
        print(f"  通过合规校验: {compliance['passed_count']} 个候选")
        print(f"  原因: 欧盟MRL裕度较小，需要人工复核确认")
        print("="*60)
        signature = _read_signature()
        if signature.lower() == "reject":
            state["human_signature"] = None
            state["errors"] = state.get("errors", []) + ["人工拒绝放行"]
            state["finished"] = True
            logger.log_event("hil_rejected", agent="treatment")
            logger.end("treatment_agent", state, None)
            return state
        else:
            state["human_signature"] = signature
            logger.log_event("hil_approved", agent="treatment", signature=signature)

    # === Phase 3: 最终选择 ===
    passed_candidates = [r for r in compliance["candidates_checked"] if r["all_passed"]]
    if not passed_candidates:
        state["errors"] = state.get("errors", []) + ["所有候选均未通过合规校验"]
        state["finished"] = True
        logger.end("treatment_agent", state, None)
        return state

    user_input_p3 = f"""通过合规校验的候选：
{passed_candidates}

合规求解器总报告：{compliance}

业务上下文：{business}
人工签字：{state.get('human_signature', '不需要')}

请选择最优方案并给出完整处方。"""

    p3_output = call_llm(SELECTION_PROMPT, user_input_p3, temperature=0.2)
    state["final_prescription"] = p3_output.get("final_prescription", {})
    state["agent_trail"] = state.get("agent_trail", []) + [{
        "agent": "treatment",
        "summary": p3_output.get("reasoning", "")
    }]

    logger.end("treatment_agent", state, p3_output)
    return state
