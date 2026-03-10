# -*- coding: utf-8 -*-
"""
基于 flatlib 的当日星盘计算服务。
提供完整的星盘数据计算，包括行星位置、角度点、宫位和相位。
"""

from datetime import date
from typing import Any
from functools import lru_cache

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const, aspects

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


# 星座英文 -> 中文名称
SIGN_NAMES_CN = {
    const.ARIES: "白羊座",
    const.TAURUS: "金牛座",
    const.GEMINI: "双子座",
    const.CANCER: "巨蟹座",
    const.LEO: "狮子座",
    const.VIRGO: "处女座",
    const.LIBRA: "天秤座",
    const.SCORPIO: "天蝎座",
    const.SAGITTARIUS: "射手座",
    const.CAPRICORN: "摩羯座",
    const.AQUARIUS: "水瓶座",
    const.PISCES: "双鱼座",
}


ASPECT_TYPE_NAMES = {
    const.CONJUNCTION: {"cn": "合相", "en": "Conjunction"},
    const.SEXTILE: {"cn": "六合", "en": "Sextile"},
    const.SQUARE: {"cn": "四分相", "en": "Square"},
    const.TRINE: {"cn": "三分相", "en": "Trine"},
    const.OPPOSITION: {"cn": "对分相", "en": "Opposition"},
}


# 【新增】宫位 ID 到中文/英文展示名
HOUSE_NAMES = {
    const.HOUSE1: {"cn": "第 1 宫", "en": "House 1"},
    const.HOUSE2: {"cn": "第 2 宫", "en": "House 2"},
    const.HOUSE3: {"cn": "第 3 宫", "en": "House 3"},
    const.HOUSE4: {"cn": "第 4 宫", "en": "House 4"},
    const.HOUSE5: {"cn": "第 5 宫", "en": "House 5"},
    const.HOUSE6: {"cn": "第 6 宫", "en": "House 6"},
    const.HOUSE7: {"cn": "第 7 宫", "en": "House 7"},
    const.HOUSE8: {"cn": "第 8 宫", "en": "House 8"},
    const.HOUSE9: {"cn": "第 9 宫", "en": "House 9"},
    const.HOUSE10: {"cn": "第 10 宫", "en": "House 10"},
    const.HOUSE11: {"cn": "第 11 宫", "en": "House 11"},
    const.HOUSE12: {"cn": "第 12 宫", "en": "House 12"},
}


def _format_tz(hours: int) -> str:
    """将时区小时转为 flatlib 需要的字符串，如 +08:00。"""
    sign = "+" if hours >= 0 else "-"
    h = abs(hours)
    return f"{sign}{h:02d}:00"


def _build_chart(
    chart_date: date,
    city: str,
    time_str: str,
) -> tuple[Chart, float, float, int]:
    """构建 flatlib Chart，并返回经纬度和时区。"""
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
    return chart, lat, lon, tz_hours


@lru_cache(maxsize=1000)
def get_daily_chart(
    chart_date: date,
    city: str,
    time_str: str = "12:00",
) -> dict[str, Any]:
    """
    计算指定日期、指定城市的星盘数据。

    :param chart_date: 日期
    :param city: 城市名称，如「广州」
    :param time_str: 当天时刻，默认 "12:00"（中午）
    :return: 包含行星位置、上升/天顶、宫位、月相等信息的字典
    """
    chart, lat, lon, tz_hours = _build_chart(chart_date, city, time_str)

    # 行星与虚点
    planets = []
    for obj in chart.objects:
        name_info = OBJECT_NAMES.get(obj.id, {"cn": str(obj.id), "en": str(obj.id)})
        try:
            movement = obj.movement()
        except (AttributeError, ValueError):
            movement = "Direct"
        planets.append(
            {
                "id": obj.id,
                "name_cn": name_info["cn"],
                "name_en": name_info["en"],
                "sign": obj.sign,
                "sign_lon": round(obj.signlon, 4),
                "longitude": round(obj.lon, 4),
                "latitude": round(getattr(obj, "lat", 0) or 0, 6),
                "speed": round(getattr(obj, "lonspeed", 0) or 0, 6),
                "movement": movement,
            }
        )

    # 上升点与天顶
    angles = []
    for aid, label_cn, label_en in [
        (const.ASC, "上升点", "Ascendant"),
        (const.MC, "天顶", "MC"),
    ]:
        try:
            angle = chart.get(aid)
            angles.append(
                {
                    "id": aid,
                    "name_cn": label_cn,
                    "name_en": label_en,
                    "sign": angle.sign,
                    "sign_lon": round(angle.signlon, 4),
                    "longitude": round(angle.lon, 4),
                }
            )
        except (AttributeError, ValueError):
            pass

    # 【新增】12 宫位数据
    houses = []
    for i in range(1, 13):
        house_id = getattr(const, f'HOUSE{i}')
        house_name_info = HOUSE_NAMES.get(house_id, {"cn": f"第{i}宫", "en": f"House {i}"})
        try:
            house = chart.get(house_id)
            houses.append(
                {
                    "house_number": i,
                    "name_cn": house_name_info["cn"],
                    "name_en": house_name_info["en"],
                    "sign": house.sign,
                    "sign_lon": round(house.signlon, 4),
                    "longitude": round(house.lon, 4),
                }
            )
        except (AttributeError, ValueError):
            # 如果某个宫位获取失败，仍然保留占位信息
            houses.append(
                {
                    "house_number": i,
                    "name_cn": house_name_info["cn"],
                    "name_en": house_name_info["en"],
                    "sign": None,
                    "sign_lon": None,
                    "longitude": None,
                }
            )

    # 月相
    try:
        moon_phase = chart.getMoonPhase()
    except (AttributeError, ValueError):
        moon_phase = None

    return {
        "date": chart_date.isoformat(),
        "city": city,
        "location": {
            "lat": lat,
            "lon": lon,
            "timezone": f"UTC{_format_tz(tz_hours)}",
        },
        "planets": planets,
        "angles": angles,
        "houses": houses,  # 【新增】宫位数据
        "moon_phase": moon_phase,
        "is_diurnal": chart.isDiurnal(),
    }


@lru_cache(maxsize=1000)
def get_daily_aspects(
    chart_date: date,
    city: str,
    time_str: str = "12:00",
) -> dict[str, Any]:
    """
    计算指定日期、指定城市的主要行星相位（结构化数据）。

    :return: 包含所有行星两两之间主要相位的列表。
    """
    chart, lat, lon, tz_hours = _build_chart(chart_date, city, time_str)

    objs = list(chart.objects)
    aspect_items: list[dict[str, Any]] = []

    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            obj1 = objs[i]
            obj2 = objs[j]
            asp = aspects.getAspect(obj1, obj2, const.MAJOR_ASPECTS)
            if not asp.exists():
                continue

            type_info = ASPECT_TYPE_NAMES.get(
                asp.type,
                {"cn": "未知相位", "en": "Unknown"},
            )

            name1 = OBJECT_NAMES.get(obj1.id, {"cn": str(obj1.id), "en": str(obj1.id)})
            name2 = OBJECT_NAMES.get(obj2.id, {"cn": str(obj2.id), "en": str(obj2.id)})

            aspect_items.append(
                {
                    "object1": {
                        "id": obj1.id,
                        "name_cn": name1["cn"],
                        "name_en": name1["en"],
                        "sign": obj1.sign,
                        "sign_lon": round(obj1.signlon, 4),
                    },
                    "object2": {
                        "id": obj2.id,
                        "name_cn": name2["cn"],
                        "name_en": name2["en"],
                        "sign": obj2.sign,
                        "sign_lon": round(obj2.signlon, 4),
                    },
                    "aspect": {
                        "type_angle": asp.type,
                        "type_cn": type_info["cn"],
                        "type_en": type_info["en"],
                        "orb": round(asp.orb, 4),
                        "movement": asp.movement(),
                        "direction": asp.direction,
                        "condition": asp.condition,
                        "active_id": asp.active.id,
                        "passive_id": asp.passive.id,
                        "mutual_in_orb": asp.mutualAspect(),
                    },
                }
            )

    return {
        "date": chart_date.isoformat(),
        "city": city,
        "location": {
            "lat": lat,
            "lon": lon,
            "timezone": f"UTC{_format_tz(tz_hours)}",
        },
        "aspects": aspect_items,
    }


@lru_cache(maxsize=1000)
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
    :return: 星盘数据字典，附带太阳星座等摘要
    """
    data = get_daily_chart(birth_date, city, time_str=birth_time)

    sun_sign_en = None
    for obj in data.get("planets", []):
        if obj.get("id") == const.SUN:
            sun_sign_en = obj.get("sign")
            break

    if sun_sign_en:
        sun_sign_cn = SIGN_NAMES_CN.get(sun_sign_en, sun_sign_en)
    else:
        sun_sign_cn = None

    data["summary"] = {
        "sun_sign_en": sun_sign_en,
        "sun_sign_cn": sun_sign_cn,
    }
    return data
