"""
Supervisor: 决定下一个该执行的Agent。
本MVP采用简化的状态机路由（基于state字段），后续可升级为LLM路由。
"""


def supervisor(state: dict) -> str:
    """返回下一个节点名称，'__end__' 表示结束"""
    if state.get("finished"):
        return "__end__"

    if not state.get("flight_plan"):
        return "patrol"

    if not state.get("diagnosis"):
        return "diagnosis"

    if not state.get("causal_analysis"):
        return "causal"

    if not state.get("final_prescription"):
        return "treatment"

    if not state.get("report_farmer"):
        return "report"

    return "__end__"
