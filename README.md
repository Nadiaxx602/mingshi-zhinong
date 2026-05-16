# 茗视智农 · 山地茶园多Agent协同决策系统

> 2026 辽宁省"中软国际--卓越杯" AI 挑战赛参赛作品 · 演示原型 v1.0.0-beta

**在线演示**：`https://<你的用户名>.github.io/<仓库名>/` *(部署 GitHub Pages 后填入)*

---

## 系统简介

针对山地茶园场景下的病虫害识别、合规校验、出口订单决策与多角色信息触达，
构建一个**五 Agent 协同**的决策系统原型：

| Agent | 职责 |
|---|---|
| 巡检 Agent | 无人机仿地航线规划与安全包络校验 |
| 诊断 Agent | K230 边缘端推理结果综合、NDVI 双流交叉验证 |
| 溯源 Agent | Chain-of-Causality 推理（确认 → 检索 → 解释 → 预测） |
| 决策 Agent | LLM 候选生成 + 确定性求解器硬约束校验 + HIL 人工签字 |
| 报告 Agent | 三套 Persona（茶农 / 管理者 / 政府）定制化交付 |

## 核心创新

1. **LLM 与确定性求解器分离** — LLM 生成候选，Python 求解器执行禁用清单/PHI/MRL 硬约束，避免幻觉违规处方
2. **HIL 人工签字机制** — 决策风险等级 high/critical 时暂停等待签字（欧盟出口订单 MRL 裕度 < 5% 触发）
3. **三套 Persona 报告** — 同一份决策结果输出茶农口语化版、管理者 KPI 仪表盘版、政府监管台账版

## 技术栈

- 前端：HTML + Tailwind CSS + Alpine.js + Lucide Icons + 内联 SVG
- 后端：Python 3.10+ · LangGraph · DeepSeek API (`deepseek-v4-flash`)
- 部署：GitHub Pages（静态演示版，前端回放预录 trace）

## 本地运行后端

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# 复制 .env.example 为 .env 并填入 DEEPSEEK_API_KEY
python run_case_b.py        # 跑完会生成 output/trace_caseB.json
python -m http.server 8000  # 本地启前端
```

浏览器打开 `http://localhost:8000/`，输入演示账号：
- `DEMO000` → 主面板（完整五 Agent 流程 + HIL）
- `ZHANG001` → 茶农视图
- `ADMIN888` → 管理者仪表盘

## 部署演示版到 GitHub Pages

仓库 Settings → Pages → Source 选 `main` 分支 `/ (root)` → Save。约 1-3 分钟后访问 `https://<你的用户名>.github.io/<仓库名>/`。
