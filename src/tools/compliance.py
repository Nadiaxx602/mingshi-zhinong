"""
LLM 与确定性求解器分离 —— 这是 茗视智农 的核心安全设计：
LLM 生成候选方案，Python 求解器执行硬约束校验，避免 LLM "自由发挥"产生违规处方。
"""
from datetime import datetime, timedelta
from .pesticide import load_banned_list, load_mrl_database


def check_banned(pesticide_name: str) -> dict:
    """茶树禁用清单校验"""
    banned = load_banned_list()
    is_banned = any(b in pesticide_name for b in banned)
    return {
        "passed": not is_banned,
        "rule": "GB 2763-2026 茶树禁用清单",
        "matched": [b for b in banned if b in pesticide_name] if is_banned else []
    }


def check_phi(pesticide: dict, harvest_date: str) -> dict:
    """安全间隔期校验"""
    phi_days = pesticide.get("phi_days", 0)
    today = datetime.now().date()
    harvest = datetime.fromisoformat(harvest_date).date()
    days_until_harvest = (harvest - today).days
    passed = days_until_harvest >= phi_days
    return {
        "passed": passed,
        "rule": "安全间隔期 (PHI)",
        "phi_days": phi_days,
        "days_until_harvest": days_until_harvest,
        "earliest_harvest_date": (today + timedelta(days=phi_days)).isoformat(),
    }


def check_mrl(pesticide: dict, country: str = "CN") -> dict:
    """农药残留限值校验"""
    mrl_db = load_mrl_database()
    active_ingredient = pesticide.get("active_ingredient", "")

    if country == "CN":
        limits = mrl_db.get("china_gb2763_2026", {})
        standard_name = "GB 2763-2026 国内MRL"
    elif country == "EU":
        limits = mrl_db.get("eu_511", {})
        standard_name = "欧盟 EC 396/2005 MRL"
    else:
        return {"passed": False, "rule": f"未知国家代码 {country}"}

    if active_ingredient not in limits:
        return {
            "passed": False,
            "rule": standard_name,
            "reason": f"{active_ingredient} 不在 {country} 茶叶许可清单",
        }

    limit_mg_kg = limits[active_ingredient]
    predicted_residue = pesticide.get("expected_residue_mg_kg", limit_mg_kg * 0.5)
    passed = predicted_residue <= limit_mg_kg

    return {
        "passed": passed,
        "rule": standard_name,
        "active_ingredient": active_ingredient,
        "limit_mg_kg": limit_mg_kg,
        "predicted_residue_mg_kg": predicted_residue,
        "margin": round(limit_mg_kg - predicted_residue, 4),
    }


def check_organic(pesticide: dict) -> dict:
    """有机认证兼容性"""
    is_organic = pesticide.get("organic_certified", False)
    return {
        "passed": is_organic,
        "rule": "有机茶认证 (NOP/EU Organic)",
        "compatible": is_organic,
    }


def solve(candidates: list[dict], context: dict) -> dict:
    """
    对每个候选农药执行全部硬约束校验。
    返回完整的合规报告，决策Agent基于此选择最优。
    """
    results = []
    for c in candidates:
        checks = {
            "banned_list": check_banned(c["name"]),
            "phi": check_phi(c, context["harvest_date"]),
            "mrl_china": check_mrl(c, "CN"),
        }
        if context.get("export_market") == "EU":
            checks["mrl_eu"] = check_mrl(c, "EU")
        if context.get("is_organic"):
            checks["organic_compat"] = check_organic(c)

        all_passed = all(v.get("passed", False) for v in checks.values())

        # 风险等级判定
        if not all_passed:
            risk_level = "rejected"
        elif checks.get("mrl_eu", {}).get("margin", 1.0) < 0.05:
            risk_level = "high"
        elif context.get("export_market") == "EU":
            risk_level = "medium"
        else:
            risk_level = "low"

        results.append({
            "pesticide_id": c["id"],
            "pesticide_name": c["name"],
            "checks": checks,
            "all_passed": all_passed,
            "risk_level": risk_level,
        })

    passed_candidates = [r for r in results if r["all_passed"]]
    overall_risk = max(
        ["rejected", "low", "medium", "high"].index(r["risk_level"])
        for r in results
    )
    overall_risk_label = ["rejected", "low", "medium", "high"][overall_risk]

    return {
        "candidates_checked": results,
        "passed_count": len(passed_candidates),
        "rejected_count": len(results) - len(passed_candidates),
        "overall_risk_level": overall_risk_label,
        "requires_human_approval": overall_risk_label in ["high"],
    }
