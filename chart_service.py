# -*- coding: utf-8 -*-
"""基于 flatlib 的当日星盘计算服务。"""

from datetime import date
from typing import Any

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

from config import get_city_coords


# 行星 ID 到中文/英文展示名
OBJECT_NAMES = {
    const.SUN: {"cn": "太阳", "en": "Sun"},
    const.MOON: {"cn": "月亮", "en": "Moon"},
    const.MERCURY: {"cn": "水星", "en": "Mercury"},
    const.VENUS: {"cn": "金星", "en": "Venus"},
    const.MARS: {"cn": "火星", "en": "Mars"},
    const.JUPITER: {"cn": "木星", "en": "Jupiter"},
    const.SATURN: {"cn": "土星", "en": "Saturn"},
    const.URANUS: {"cn": "天王星", "en": "Uranus"},
    const.NEPTUNE: {"cn": "海王星", "en": "Neptune"},
    const.PLUTO: {"cn": "冥王星", "en": "Pluto"},
    const.NORTH_NODE: {"cn": "北交点", "en": "North Node"},
    const.SOUTH_NODE: {"cn": "南交点", "en": "South Node"},
    const.SYZYGY: {"cn": "朔望点", "en": "Syzygy"},
    const.PARS_FORTUNA: {"cn": "福点", "en": "Part of Fortune"},
}


def _format_tz(hours: int) -> str:
    """将时区小时转为 flatlib 需要的字符串，如 +08:00。"""
    sign = "+" if hours >= 0 else "-"
    h = abs(hours)
    return f"{sign}{h:02d}:00"


def get_daily_chart(
    chart_date: date,
    city: str,
    time_str: str = "12:00",
) -> dict[str, Any]:
    """
    计算指定日期、指定城市（当日中午）的星盘数据。

    :param chart_date: 日期
    :param city: 城市名称，如「广州」
    :param time_str: 当天时刻，默认 "12:00"（中午）
    :return: 包含行星位置、上升/天顶、月相等信息的字典
    """
    coords = get_city_coords(city)
    if not coords:
        raise ValueError(
            f"暂不支持城市「{city}」，请检查拼写，或先调用 /api/cities?q=城市名 搜索可用城市。"
        )
    lat, lon, tz_hours = coords
    tz_str = _format_tz(tz_hours)

    date_str = chart_date.strftime("%Y/%m/%d")
    flat_date = Datetime(date_str, time_str, tz_str)
    pos = GeoPos(lat, lon)
    chart = Chart(flat_date, pos)

    # 行星与虚点
    planets = []
    for obj in chart.objects:
        name_info = OBJECT_NAMES.get(obj.id, {"cn": str(obj.id), "en": str(obj.id)})
        try:
            movement = obj.movement()
        except Exception:
            movement = "Direct"
        planets.append({
            "id": obj.id,
            "name_cn": name_info["cn"],
            "name_en": name_info["en"],
            "sign": obj.sign,
            "sign_lon": round(obj.signlon, 4),
            "longitude": round(obj.lon, 4),
            "latitude": round(getattr(obj, "lat", 0) or 0, 6),
            "speed": round(getattr(obj, "lonspeed", 0) or 0, 6),
            "movement": movement,
        })

    # 上升点与天顶
    angles = []
    for aid, label_cn, label_en in [
        (const.ASC, "上升点", "Ascendant"),
        (const.MC, "天顶", "MC"),
    ]:
        try:
            angle = chart.get(aid)
            angles.append({
                "id": aid,
                "name_cn": label_cn,
                "name_en": label_en,
                "sign": angle.sign,
                "sign_lon": round(angle.signlon, 4),
                "longitude": round(angle.lon, 4),
            })
        except Exception:
            pass

    # 月相
    try:
        moon_phase = chart.getMoonPhase()
    except Exception:
        moon_phase = None

    return {
        "date": chart_date.isoformat(),
        "city": city,
        "location": {"lat": lat, "lon": lon, "timezone": f"UTC{_format_tz(tz_hours)}"},
        "planets": planets,
        "angles": angles,
        "moon_phase": moon_phase,
        "is_diurnal": chart.isDiurnal(),
    }


def get_natal_chart(
    birth_date: date,
    birth_time: str,
    city: str,
) -> dict[str, Any]:
    """
    计算本命盘（出生时刻星盘）。

    :param birth_date: 出生日期
    :param birth_time: 出生时间，如 "14:30"
    :param city: 出生地城市
    :return: 星盘数据字典，结构同 get_daily_chart
    """
    return get_daily_chart(birth_date, city, time_str=birth_time)
