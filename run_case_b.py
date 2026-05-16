"""运行 Case B：欧盟MRL出口订单场景"""
import sys
import json
from pathlib import Path

# 保证 Windows 中文输出
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.graph import build_graph
from src.trace_logger import get_logger


def main():
    print("="*60)
    print(" 茗视智农 · 五Agent协同决策系统 · Case B 演示")
    print(" 场景：山地茶园·茶炭疽病·欧盟出口订单")
    print("="*60)

    # 加载初始状态
    with open("data/case_b.json", "r", encoding="utf-8") as f:
        initial_state = json.load(f)

    # 构建并运行图
    graph = build_graph()
    final_state = graph.invoke(initial_state, {"recursion_limit": 30})

    # 导出轨迹
    logger = get_logger()
    output_path = "output/trace_caseB.json"
    logger.dump(output_path)

    print("\n" + "="*60)
    print(" 演示结束")
    print("="*60)

    # 简要打印结果
    print(f"\n【诊断】{final_state.get('diagnosis', {}).get('disease', 'N/A')} "
          f"严重度 {final_state.get('diagnosis', {}).get('severity', 'N/A')} 级")

    rx = final_state.get("final_prescription", {})
    if rx:
        print(f"\n【最终处方】{rx.get('pesticide_name')}")
        print(f"  稀释：{rx.get('dilution_ratio')}, 剂量：{rx.get('dose_ml_per_mu')} ml/亩")
        print(f"  最早采茶日：{rx.get('earliest_harvest_date')}")

    farmer = final_state.get("report_farmer", "")
    if farmer:
        print(f"\n【茶农版报告】\n{farmer}")

    print(f"\n【轨迹文件】{output_path}")
    print(f"【事件数】{len(logger.events)}\n")


if __name__ == "__main__":
    main()
