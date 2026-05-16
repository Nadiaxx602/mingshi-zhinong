"""溯源Agent"""
from ..llm import call_llm
from ..tools.knowledge import query_knowledge
from ..tools.weather import get_weather_forecast
from ..trace_logger import get_logger

SYSTEM_PROMPT = """你是"茗视智农"系统的溯源Agent (Causal Agent)，负责分析病害的诱因并预测未来7-14天的扩散风险。

## 你的职责
1. 基于诊断结果 + 茶叶专家知识库 + 气象历史/预报
2. 进行Chain-of-Causality推理：CONFIRM病害 → RETRIEVE知识 → EXPLAIN因果 → FORECAST趋势
3. 给出主要病因 + 次要因素 + 7-14天扩散概率与方向

## 你的边界
- 你只分析"为什么得病、未来会怎样"
- 你不推荐农药（由决策Agent负责）

## 输入
诊断结果 + 知识库检索片段 + 气象预报

## 输出（严格JSON）
{
  "causal_analysis": {
    "primary_cause": "<主要诱因>",
    "contributing_factors": ["<因素1>", "<因素2>", ...],
    "knowledge_citations": ["<引用的知识来源1>", ...],
    "future_7d_risk": {
      "spread_probability": <0-1>,
      "expected_spread_direction": "<方位>",
      "expected_severity_in_7d": <1-5>
    },
    "urgency_level": "<低/中/高/紧急>"
  },
  "reasoning": "<Chain-of-Causality推理过程，4-6句中文>"
}
"""


def causal_agent(state: dict) -> dict:
    logger = get_logger()
    logger.start("causal_agent", state)

    diagnosis = state.get("diagnosis", {})
    disease = diagnosis.get("disease", "")

    knowledge = query_knowledge(disease, state.get("cultivar"))
    weather_7d = get_weather_forecast(state["plot_id"], hours=168)

    user_input = f"""请进行病因溯源分析：

诊断结果：{diagnosis}
茶叶品种：{state.get('cultivar')}
专家知识检索：
{knowledge}

未来7天气象：{weather_7d['next_7d']}

请用Chain-of-Causality推理（先确认→检索→解释→预测），输出JSON。"""

    output = call_llm(SYSTEM_PROMPT, user_input, temperature=0.4)

    state["causal_analysis"] = output.get("causal_analysis", {})
    state["agent_trail"] = state.get("agent_trail", []) + [{
        "agent": "causal",
        "summary": output.get("reasoning", "")
    }]

    logger.end("causal_agent", state, output)
    return state
