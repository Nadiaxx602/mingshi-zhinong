"""报告Agent —— 三套Persona报告"""
from ..llm import call_llm
from ..trace_logger import get_logger

SYSTEM_PROMPT = """你是"茗视智农"系统的报告Agent (Report Agent)，负责将技术化的决策结果翻译成三种用户能消费的格式。

## 三种Persona
1. **茶农版** (farmer)：方言友好的口语化文本（不超过150字），告诉茶农"做什么/什么时候/注意什么"
2. **管理者版** (manager)：合作社/茶企管理者关心的KPI仪表盘数据
3. **政府版** (government)：监管部门所需的农事台账+合规凭证

## 工作方式
- 所有数值字段必须来自上游决策结果，你不创造数值，只翻译表达
- 茶农版要避免术语：用"打药"不用"施药"，用"等14天再采"不用"PHI=14天"

## 输出（严格JSON）
{
  "report_farmer": "<茶农口语化文字，控制在150字内>",
  "report_manager": {
    "kpi_summary": {
      "affected_area_mu": <数字>,
      "intervention_cost_estimate_yuan": <数字>,
      "expected_yield_protection_pct": <数字>,
      "compliance_status": "<达标/警示>",
      "next_harvest_date": "<日期>"
    },
    "action_items": ["<行动1>", "<行动2>"]
  },
  "report_government": {
    "filing_id": "<台账编号，格式 TEA-yyyy-mm-dd-XXX>",
    "operation_record": {
      "date": "<施药日期>",
      "plot_id": "<地块ID>",
      "pesticide_name": "<农药名>",
      "registration_no": "<登记号>",
      "dose": "<剂量>",
      "operator_signature": "<签字>"
    },
    "compliance_certificate": {
      "gb2763_2026": "通过",
      "eu_mrl": "通过/不适用",
      "phi_compliance": "通过",
      "banned_list_compliance": "通过"
    }
  }
}
"""


def report_agent(state: dict) -> dict:
    logger = get_logger()
    logger.start("report_agent", state)

    user_input = f"""请生成三套Persona报告：

最终处方：{state['final_prescription']}
地块ID：{state['plot_id']}
诊断：{state['diagnosis']}
业务上下文：{state['business_context']}
人工签字：{state.get('human_signature', '系统自动放行')}

请输出三种格式的报告JSON。"""

    output = call_llm(SYSTEM_PROMPT, user_input, temperature=0.5)

    state["report_farmer"] = output.get("report_farmer")
    state["report_manager"] = output.get("report_manager")
    state["report_government"] = output.get("report_government")
    state["finished"] = True

    logger.end("report_agent", state, output)
    return state
