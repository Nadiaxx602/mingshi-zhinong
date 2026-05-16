"""五Agent协同的共享状态定义"""
from typing import TypedDict, Literal, Optional


class TeaGardenState(TypedDict, total=False):
    """五Agent协同的共享状态"""
    # === 元数据 ===
    task_id: str
    mission_type: Literal["routine", "alert", "export_audit"]
    plot_id: str
    timestamp: str

    # === 业务上下文 ===
    cultivar: str
    elevation_m: int
    business_context: dict

    # === 巡检Agent 写入 ===
    flight_plan: Optional[dict]
    safety_check: Optional[dict]

    # === 诊断Agent 写入 ===
    perception_raw: list[dict]
    diagnosis: Optional[dict]
    needs_vlm_review: bool

    # === 溯源Agent 写入 ===
    causal_analysis: Optional[dict]

    # === 决策Agent 写入 ===
    candidate_treatments: list[dict]
    compliance_report: Optional[dict]
    final_prescription: Optional[dict]
    requires_human_approval: bool
    human_signature: Optional[str]

    # === 报告Agent 写入 ===
    report_farmer: Optional[str]
    report_manager: Optional[dict]
    report_government: Optional[dict]

    # === 全局 ===
    agent_trail: list[dict]
    errors: list[str]
    next_agent: Optional[str]
    finished: bool
