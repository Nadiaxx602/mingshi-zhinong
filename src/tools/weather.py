"""气象工具（mock，演示用）"""


def get_weather_forecast(plot_id: str, hours: int = 168) -> dict:
    """模拟未来气象预报。Day 1 演示用合成数据。"""
    return {
        "plot_id": plot_id,
        "forecast_hours": hours,
        "next_24h": {"temp_c": [18, 22], "humidity": 78, "wind_ms": 3.2, "rain_mm": 0},
        "next_7d": {
            "temp_range_c": [16, 26],
            "rain_days": 2,
            "high_humidity_days": 4,
            "disease_pressure": "moderate-high"
        }
    }
