"""地理信息工具（mock，演示用）"""


def get_plot_info(plot_id: str) -> dict:
    return {
        "plot_id": plot_id,
        "area_mu": 8.6,
        "elevation_m": 850,
        "slope_deg": 23,
        "aspect": "southeast",
        "cultivar": "金牡丹",
        "planting_year": 2018,
    }
