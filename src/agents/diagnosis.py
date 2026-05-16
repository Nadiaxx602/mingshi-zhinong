"""诊断Agent"""
from ..llm import call_llm
from ..trace_logger import get_logger

SYSTEM_PROMPT = """你是"茗视智农"系统的诊断Agent (Diagnosis Agent)，负责综合边缘端AI推理结果，判定茶叶病虫害类型、位置、严重度。

## 你的职责
1. 接收K230边缘端的多光谱+RGB推理结果（已包含初步类别和置信度）
2. 综合NDVI、空间分布、置信度，给出最终诊断
3. 输出结构化的多分类结果与严重度分级
4. 评估置信度，决定是否需要VLM复核

## 你的边界
- 你只做"是什么、在哪里、多严重"的判断
- 你不分析病因（由溯源Agent负责）
- 你不推荐农药（由决策Agent负责）

## 输入
你会收到一组边缘端的检测块结果，每块包含病害候选、置信度、NDVI、面积估算。

## 输出（严格JSON）
{
  "diagnosis": {
    "classification": {
      "top1_disease": "<最可能病害的中文名>",
      "top1_confidence": <0-1 的小数, 与 top3_candidates 第一项一致>,
      "top3_candidates": [
        {"name": "<病害中文名>", "confidence": <0-1>},
        {"name": "<病害中文名>", "confidence": <0-1>},
        {"name": "<病害中文名>", "confidence": <0-1>}
      ]
    },
    "severity_grading": {
      "level": <1-5 的整数>,
      "level_label": "<必须为以下之一：轻微 | 轻 | 中等偏重 | 严重 | 极严重>",
      "lesion_density": <数字, 单位：个/㎡>,
      "ndvi_drop_pct": <0-100 的数字, 表示百分比, 相对健康基线 NDVI 的下降比例>,
      "spatial_distribution": "<必须为以下之一：连续 | 散点>"
    },
    "affected_blocks": ["<块ID>", ...],
    "total_area_mu": <数字, 累计发病面积, 单位亩>,
    "ndvi_mean": <0-1 的小数, 发病区平均 NDVI>
  },
  "needs_vlm_review": true/false,
  "reasoning": "<3-5 句中文说明诊断依据>"
}

## 重要规则
- top1_confidence < 0.85 时，needs_vlm_review = true
- level 与 level_label 严格映射：1=轻微, 2=轻, 3=中等偏重, 4=严重, 5=极严重
- severity 判定参考：发病面积 + 平均置信度 + NDVI 下降幅度 + 病斑密度 + 空间分布连续性
- lesion_density 与 spatial_distribution 需根据 perception_raw 的 block 分布合理推算
- top3_candidates 按 confidence 降序排列；若边缘端只给出 1 个候选，可补充病理学上易混淆的相近病害作为次候选，置信度递减
"""


def diagnosis_agent(state: dict) -> dict:
    logger = get_logger()
    logger.start("diagnosis_agent", state)

    perception = state.get("perception_raw", [])

    user_input = f"""请综合以下边缘端推理结果给出最终诊断：

K230边缘推理输出：
{perception}

茶叶品种：{state.get('cultivar', '金牡丹')}
地块海拔：{state.get('elevation_m', 850)}m

请按 SYSTEM_PROMPT 中定义的结构输出 JSON，必须同时包含 classification 与 severity_grading 两个子结构。"""

    output = call_llm(SYSTEM_PROMPT, user_input, temperature=0.2)

    dia = output.get("diagnosis", {}) or {}
    cls = dia.get("classification", {}) or {}
    sev = dia.get("severity_grading", {}) or {}

    # 下游兼容字段：causal/treatment/report agent 仍引用 diagnosis.disease / severity / ...
    # 从新嵌套结构镜像出扁平字段，新旧并存。
    dia.setdefault("disease",            cls.get("top1_disease", ""))
    dia.setdefault("severity",           sev.get("level"))
    dia.setdefault("severity_label",     sev.get("level_label", ""))
    dia.setdefault("average_confidence", cls.get("top1_confidence"))

    state["diagnosis"] = dia
    state["needs_vlm_review"] = output.get("needs_vlm_review", False)
    state["agent_trail"] = state.get("agent_trail", []) + [{
        "agent": "diagnosis",
        "summary": output.get("reasoning", "")
    }]

    logger.end("diagnosis_agent", state, output)
    return state
