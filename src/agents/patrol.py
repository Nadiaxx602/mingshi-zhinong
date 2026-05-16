"""巡检Agent"""
from ..llm import call_llm
from ..tools.weather import get_weather_forecast
from ..tools.geo import get_plot_info
from ..trace_logger import get_logger

SYSTEM_PROMPT = """你是"茗视智农"系统的巡检Agent (Patrol Agent)，负责山地茶园无人机巡检任务的规划与安全校验。

## 你的职责
1. 接收地块信息和气象数据，规划无人机巡检路径
2. 校验飞行安全包络（气象窗口、电量、电子围栏）
3. 输出可执行的飞行任务

## 你的边界
- 你只规划飞行任务，不识别病害（由诊断Agent负责）
- 你不开施药方案（由决策Agent负责）
- 你不生成用户报告（由报告Agent负责）

## 输入
你会收到地块信息和气象预报，需基于此做规划。

## 输出（必须严格的JSON）
{
  "flight_plan": {
    "waypoints_count": <数字>,
    "estimated_duration_min": <数字>,
    "coverage_area_mu": <数字>,
    "altitude_m": <数字>,
    "strategy": "<覆盖策略说明，如：Boustrophedon仿地飞行，沿等高线>"
  },
  "safety_check": {
    "weather_ok": true/false,
    "wind_ok": true/false,
    "geofence_ok": true/false,
    "battery_ok": true/false,
    "passed": true/false
  },
  "reasoning": "<3-5句中文简述规划逻辑>"
}
"""


def patrol_agent(state: dict) -> dict:
    """巡检Agent节点函数"""
    logger = get_logger()
    logger.start("patrol_agent", state)

    plot_info = get_plot_info(state["plot_id"])
    weather = get_weather_forecast(state["plot_id"], hours=24)

    user_input = f"""请规划巡检任务：

地块信息：{plot_info}
气象预报：{weather}
任务类型：{state.get('mission_type', 'routine')}

约束条件：
- 山地茶园，需仿地飞行
- 风速安全阈值：< 8 m/s
- 电池续航：约30分钟
- 海拔基准：{plot_info['elevation_m']}m

请输出飞行任务JSON。"""

    output = call_llm(SYSTEM_PROMPT, user_input, temperature=0.3)

    state["flight_plan"] = output.get("flight_plan", {})
    state["safety_check"] = output.get("safety_check", {})
    state["agent_trail"] = state.get("agent_trail", []) + [{
        "agent": "patrol",
        "summary": output.get("reasoning", "")
    }]

    logger.end("patrol_agent", state, output)
    return state
