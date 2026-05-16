"""LangGraph 五Agent协同图构建"""
from langgraph.graph import StateGraph, END
from .state import TeaGardenState
from .agents.patrol import patrol_agent
from .agents.diagnosis import diagnosis_agent
from .agents.causal import causal_agent
from .agents.treatment import treatment_agent
from .agents.report import report_agent
from .supervisor import supervisor


def build_graph():
    g = StateGraph(TeaGardenState)

    g.add_node("patrol", patrol_agent)
    g.add_node("diagnosis", diagnosis_agent)
    g.add_node("causal", causal_agent)
    g.add_node("treatment", treatment_agent)
    g.add_node("report", report_agent)

    # 入口：从 supervisor 路由
    g.set_conditional_entry_point(supervisor, {
        "patrol": "patrol",
        "diagnosis": "diagnosis",
        "causal": "causal",
        "treatment": "treatment",
        "report": "report",
        "__end__": END,
    })

    # 每个Agent执行完后回到supervisor
    for node in ["patrol", "diagnosis", "causal", "treatment", "report"]:
        g.add_conditional_edges(node, supervisor, {
            "patrol": "patrol",
            "diagnosis": "diagnosis",
            "causal": "causal",
            "treatment": "treatment",
            "report": "report",
            "__end__": END,
        })

    return g.compile()
