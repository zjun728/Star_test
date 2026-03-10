# -*- coding: utf-8 -*-
"""
合盘分析服务（Synastry & Composite Chart）
提供比较盘和组合盘的计算功能
"""

from datetime import date
from typing import Any, Dict, List, Optional
from functools import lru_cache

from flatlib import const, aspects
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

from config import get_city_coords
from chart_service import (
    get_natal_chart,
    SIGN_NAMES_CN,
    OBJECT_NAMES,
    ASPECT_TYPE_NAMES,
    HOUSE_NAMES,
)


def _calculate_midpoint(lon1: float, lon2: float) -> float:
    """
    计算两个经度的中点
    
    :param lon1: 第一个经度
    :param lon2: 第二个经度
    :return: 中点经度
    """
    diff = lon2 - lon1
    # 处理跨越 0 度的情况
    if abs(diff) > 180:
        if diff > 0:
            lon1 += 360
        else:
            lon2 += 360
    
    return ((lon1 + lon2) / 2) % 360


def _is_planet_in_house(planet_lon: float, house_start: float, house_end: float) -> bool:
    """
    判断行星是否落在宫位内
    
    :param planet_lon: 行星经度
    :param house_start: 宫位起始经度
    :param house_end: 宫位结束经度
    :return: 是否在宫内
    """
    # 处理跨越 0 度的情况
    if house_start > house_end:
        return planet_lon >= house_start or planet_lon <= house_end
    else:
        return house_start <= planet_lon <= house_end


def _get_sign_by_longitude(lon: float) -> str:
    """根据经度获取星座"""
    sign_index = int(lon / 30)
    signs = [
        const.ARIES, const.TAURUS, const.GEMINI,
        const.CANCER, const.LEO, const.VIRGO,
        const.LIBRA, const.SCORPIO, const.SAGITTARIUS,
        const.CAPRICORN, const.AQUARIUS, const.PISCES
    ]
    return signs[sign_index % 12]


def calculate_synastry(chart_a: Dict[str, Any], chart_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算比较盘（Synastry）
    
    :param chart_a: A 的本命盘数据
    :param chart_b: B 的本命盘数据
    :return: 比较盘数据
    """
    result = {
        "planets_in_houses": [],
        "cross_aspects": []
    }
    
    # A 的行星落入 B 的宫位
    for planet in chart_a.get("planets", []):
        planet_name = planet.get("name_cn")
        planet_id = planet.get("id")
        planet_lon = planet.get("longitude")
        
        for i, house in enumerate(chart_b.get("houses", [])):
            house_number = house.get("house_number")
            
            # 获取下一个宫位的起始位置作为当前宫位的结束
            if i < len(chart_b["houses"]) - 1:
                next_house = chart_b["houses"][i + 1]
                house_end = next_house.get("longitude", 0)
            else:
                # 第 12 宫的结束是第 1 宫的开始
                house_end = chart_b["houses"][0].get("longitude", 0)
            
            house_start = house.get("longitude")
            
            if _is_planet_in_house(planet_lon, house_start, house_end):
                result["planets_in_houses"].append({
                    "planet_owner": "A",
                    "planet_id": planet_id,
                    "planet_name": planet_name,
                    "house_owner": "B",
                    "house_number": house_number,
                    "house_sign": house.get("sign"),
                    "description": f"A 的{planet_name}落在 B 的第{house_number}宫（{HOUSE_NAMES.get(house.get('id', ''), {}).get('cn', f'第{house_number}宫')}）"
                })
    
    # B 的行星落入 A 的宫位
    for planet in chart_b.get("planets", []):
        planet_name = planet.get("name_cn")
        planet_id = planet.get("id")
        planet_lon = planet.get("longitude")
        
        for i, house in enumerate(chart_a.get("houses", [])):
            house_number = house.get("house_number")
            
            if i < len(chart_a["houses"]) - 1:
                next_house = chart_a["houses"][i + 1]
                house_end = next_house.get("longitude", 0)
            else:
                house_end = chart_a["houses"][0].get("longitude", 0)
            
            house_start = house.get("longitude")
            
            if _is_planet_in_house(planet_lon, house_start, house_end):
                result["planets_in_houses"].append({
                    "planet_owner": "B",
                    "planet_id": planet_id,
                    "planet_name": planet_name,
                    "house_owner": "A",
                    "house_number": house_number,
                    "house_sign": house.get("sign"),
                    "description": f"B 的{planet_name}落在 A 的第{house_number}宫（{HOUSE_NAMES.get(house.get('id', ''), {}).get('cn', f'第{house_number}宫')}）"
                })
    
    # 交叉相位
    planets_a = chart_a.get("planets", [])
    planets_b = chart_b.get("planets", [])
    
    for planet_a in planets_a:
        for planet_b in planets_b:
            # 简化版相位计算
            lon_a = planet_a.get("longitude", 0)
            lon_b = planet_b.get("longitude", 0)
            
            diff = abs(lon_a - lon_b)
            if diff > 180:
                diff = 360 - diff
            
            # 判断主要相位
            aspect_type = None
            orb = 0
            
            if diff <= 8:  # 合相（容许度 8 度）
                aspect_type = const.CONJUNCTION
                orb = 8 - diff
            elif 52 <= diff <= 68:  # 六分相（容许度 8 度）
                aspect_type = const.SEXTILE
                orb = 8 - abs(60 - diff)
            elif 82 <= diff <= 98:  # 四分相（容许度 8 度）
                aspect_type = const.SQUARE
                orb = 8 - abs(90 - diff)
            elif 112 <= diff <= 128:  # 三分相（容许度 8 度）
                aspect_type = const.TRINE
                orb = 8 - abs(120 - diff)
            elif 172 <= diff <= 180:  # 对分相（容许度 8 度）
                aspect_type = const.OPPOSITION
                orb = 8 - abs(180 - diff)
            
            if aspect_type:
                type_info = ASPECT_TYPE_NAMES.get(aspect_type, {"cn": "未知", "en": "Unknown"})
                result["cross_aspects"].append({
                    "person1_planet_id": planet_a.get("id"),
                    "person1_planet_name": planet_a.get("name_cn"),
                    "person2_planet_id": planet_b.get("id"),
                    "person2_planet_name": planet_b.get("name_cn"),
                    "aspect_type": aspect_type,
                    "aspect_name_cn": type_info["cn"],
                    "aspect_name_en": type_info["en"],
                    "orb": round(orb, 2),
                    "exactness": "Applying" if orb > 3 else "Separating",
                    "description": f"{planet_a.get('name_cn')}与{planet_b.get('name_cn')}{type_info['cn']}（容许度：{orb:.1f}°）"
                })
    
    return result


def calculate_composite(chart_a: Dict[str, Any], chart_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算组合盘（Composite Chart - 中点法）
    
    :param chart_a: A 的本命盘
    :param chart_b: B 的本命盘
    :return: 组合盘数据
    """
    composite = {
        "planets": [],
        "angles": [],
        "houses": []
    }
    
    # 计算行星中点
    planets_a = {p["id"]: p for p in chart_a.get("planets", [])}
    planets_b = {p["id"]: p for p in chart_b.get("planets", [])}
    
    common_planets = set(planets_a.keys()) & set(planets_b.keys())
    
    for planet_id in common_planets:
        planet_a = planets_a[planet_id]
        planet_b = planets_b[planet_id]
        
        mid_lon = _calculate_midpoint(
            planet_a.get("longitude", 0),
            planet_b.get("longitude", 0)
        )
        
        sign = _get_sign_by_longitude(mid_lon)
        sign_lon = mid_lon % 30
        
        name_info = planet_a  # 使用 A 的行星名称信息
        
        composite["planets"].append({
            "id": planet_id,
            "name_cn": name_info.get("name_cn"),
            "name_en": name_info.get("name_en"),
            "sign": sign,
            "sign_lon": round(sign_lon, 4),
            "longitude": round(mid_lon, 4)
        })
    
    # 计算角度点中点（上升点和天顶）
    if chart_a.get("angles") and chart_b.get("angles"):
        for i, angle in enumerate(["Ascendant", "MC"]):
            angle_a = next((a for a in chart_a["angles"] if a.get("id") == [const.ASC, const.MC][i]), None)
            angle_b = next((a for a in chart_b["angles"] if a.get("id") == [const.ASC, const.MC][i]), None)
            
            if angle_a and angle_b:
                mid_lon = _calculate_midpoint(
                    angle_a.get("longitude", 0),
                    angle_b.get("longitude", 0)
                )
                
                sign = _get_sign_by_longitude(mid_lon)
                sign_lon = mid_lon % 30
                
                composite["angles"].append({
                    "id": angle_a.get("id"),
                    "name_cn": angle_a.get("name_cn"),
                    "name_en": angle_a.get("name_en"),
                    "sign": sign,
                    "sign_lon": round(sign_lon, 4),
                    "longitude": round(mid_lon, 4)
                })
    
    # 简化的宫位计算（等宫制）
    if composite["angles"]:
        asc = next((a for a in composite["angles"] if a.get("id") == const.ASC), None)
        if asc:
            asc_lon = asc.get("longitude", 0)
            for i in range(1, 13):
                house_lon = (asc_lon + (i - 1) * 30) % 360
                sign = _get_sign_by_longitude(house_lon)
                sign_lon = house_lon % 30
                
                composite["houses"].append({
                    "house_number": i,
                    "name_cn": HOUSE_NAMES.get(getattr(const, f'HOUSE{i}', None), {}).get("cn", f"第{i}宫"),
                    "name_en": f"House {i}",
                    "sign": sign,
                    "sign_lon": round(sign_lon, 4),
                    "longitude": round(house_lon, 4)
                })
    
    return composite


def calculate_relationship_indicators(synastry_data: Dict[str, Any], 
                                     composite_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算关系指标（专业版评分）

    :param synastry_data: 比较盘数据
    :param composite_data: 组合盘数据
    :return: 关系指标评分
    """
    indicators = {
        "emotional_compatibility": 0,  # 情感兼容性
        "communication_score": 0,       # 沟通分数
        "physical_attraction": 0,       # 身体吸引力
        "long_term_potential": 0,       # 长期潜力
        "overall_harmony": 0            # 整体和谐度
    }
    
    # 基于行星落入宫位计分
    planets_in_houses = synastry_data.get("planets_in_houses", [])
    cross_aspects = synastry_data.get("cross_aspects", [])
    
    # 初始化各项指标分数
    emotional_score = 0
    communication_score = 0
    physical_score = 0
    long_term_score = 0
    
    # 行星落入宫位的权重配置
    house_placement_weights = {
        # 情感兼容性相关
        ("Moon", 4): 12,    # 月亮落入 4 宫（家庭宫）
        ("Moon", 7): 15,    # 月亮落入 7 宫（伴侣宫）
        ("Sun", 7): 12,     # 太阳落入 7 宫
        ("Venus", 7): 14,   # 金星落入 7 宫
        
        # 沟通分数相关
        ("Mercury", 3): 10, # 水星落入 3 宫（沟通宫）
        ("Mercury", 9): 8,  # 水星落入 9 宫（高等教育宫）
        ("Sun", 3): 7,      # 太阳落入 3 宫
        
        # 身体吸引力相关
        ("Venus", 5): 12,   # 金星落入 5 宫（恋爱宫）
        ("Mars", 5): 10,    # 火星落入 5 宫
        ("Venus", 8): 14,   # 金星落入 8 宫（性宫）
        ("Mars", 8): 13,    # 火星落入 8 宫
        
        # 长期潜力相关
        ("Saturn", 7): 15,  # 土星落入 7 宫（稳定关系）
        ("Jupiter", 7): 10, # 木星落入 7 宫（成长关系）
        ("Sun", 10): 8,     # 太阳落入 10 宫（事业合作）
    }
    
    # 处理行星落入宫位
    for entry in planets_in_houses:
        planet_name = entry["planet_name"]
        planet_id = entry["planet_id"]
        house_number = entry["house_number"]
        
        # 优先使用英文名称作为键
        key = (planet_id, house_number)
        if key not in house_placement_weights:
            # 兼容处理，尝试使用中文名称
            key = (planet_name, house_number)
        
        if key in house_placement_weights:
            weight = house_placement_weights[key]
            
            # 根据宫位和行星类型分配分数到相应指标
            if house_number in [4, 7]:
                emotional_score += weight
            if house_number in [3, 9]:
                communication_score += weight
            if house_number in [5, 8]:
                physical_score += weight
            if house_number in [7, 10]:
                long_term_score += weight
    
    # 相位权重配置
    aspect_weights = {
        # 情感兼容性相关相位
        ("Moon", "Sun"): 15,
        ("Moon", "Venus"): 14,
        ("Sun", "Venus"): 12,
        
        # 沟通相关相位
        ("Mercury", "Mercury"): 12,
        ("Mercury", "Sun"): 10,
        ("Mercury", "Moon"): 9,
        
        # 身体吸引力相关相位
        ("Mars", "Venus"): 16,
        ("Mars", "Mars"): 10,
        ("Venus", "Venus"): 8,
        
        # 长期潜力相关相位
        ("Saturn", "Sun"): 14,
        ("Saturn", "Moon"): 12,
        ("Jupiter", "Sun"): 10,
        ("Jupiter", "Moon"): 9,
    }
    
    # 处理交叉相位
    positive_aspects = [const.TRINE, const.SEXTILE, const.CONJUNCTION]
    challenging_aspects = [const.SQUARE, const.OPPOSITION]
    
    for aspect in cross_aspects:
        planet1_name = aspect["person1_planet_name"]
        planet2_name = aspect["person2_planet_name"]
        planet1_id = aspect["person1_planet_id"]
        planet2_id = aspect["person2_planet_id"]
        aspect_type = aspect["aspect_type"]
        
        # 优先使用行星ID（英文名称）
        planet1 = planet1_id
        planet2 = planet2_id
        
        # 标准化行星顺序，确保 (A, B) 和 (B, A) 被视为同一组合
        if planet1 > planet2:
            planet1, planet2 = planet2, planet1
        
        aspect_key = (planet1, planet2)
        
        if aspect_key in aspect_weights:
            base_weight = aspect_weights[aspect_key]
            
            if aspect_type in positive_aspects:
                # 吉相加分
                if planet1 in ["Moon", "Venus", "Sun"] or planet2 in ["Moon", "Venus", "Sun"]:
                    emotional_score += base_weight
                if planet1 in ["Mercury"] or planet2 in ["Mercury"]:
                    communication_score += base_weight * 0.8
                if planet1 in ["Mars", "Venus"] or planet2 in ["Mars", "Venus"]:
                    physical_score += base_weight
                if planet1 in ["Saturn", "Jupiter"] or planet2 in ["Saturn", "Jupiter"]:
                    long_term_score += base_weight
            elif aspect_type in challenging_aspects:
                # 凶相：根据行星组合调整分数
                if (planet1, planet2) == ("Mars", "Venus"):
                    # 金火刑冲有强烈吸引力
                    physical_score += base_weight * 0.7
                elif (planet1, planet2) == ("Moon", "Sun"):
                    # 日月刑冲是重要的情感挑战
                    emotional_score += base_weight * 0.5
                else:
                    # 其他凶相适当减分
                    total_score = emotional_score + communication_score + physical_score + long_term_score
                    if total_score > 50:
                        # 如果整体分数较高，凶相的负面影响较小
                        pass
                    else:
                        # 整体分数较低时，凶相的负面影响较大
                        if planet1 in ["Moon", "Venus", "Sun"] or planet2 in ["Moon", "Venus", "Sun"]:
                            emotional_score -= base_weight * 0.3
                        if planet1 in ["Mercury"] or planet2 in ["Mercury"]:
                            communication_score -= base_weight * 0.3
    
    # 组合盘分析（如果有）
    if composite_data:
        composite_planets = {p["id"]: p for p in composite_data.get("planets", [])}
        
        # 组合盘太阳和月亮的位置对关系有重要影响
        if "Sun" in composite_planets and "Moon" in composite_planets:
            emotional_score += 10
        
        # 组合盘金星的位置影响关系和谐度
        if "Venus" in composite_planets:
            physical_score += 8
        
        # 组合盘土星的位置影响长期稳定性
        if "Saturn" in composite_planets:
            long_term_score += 12
    
    # 计算各项指标的最终分数（0-100）
    max_possible = 200  # 估算的最大可能分数
    indicators["emotional_compatibility"] = min(100, max(0, int((emotional_score / max_possible) * 100)))
    indicators["communication_score"] = min(100, max(0, int((communication_score / max_possible) * 100)))
    indicators["physical_attraction"] = min(100, max(0, int((physical_score / max_possible) * 100)))
    indicators["long_term_potential"] = min(100, max(0, int((long_term_score / max_possible) * 100)))
    
    # 计算整体和谐度（加权平均）
    weights = {
        "emotional_compatibility": 0.35,
        "communication_score": 0.25,
        "physical_attraction": 0.20,
        "long_term_potential": 0.20
    }
    
    overall = 0
    for key, weight in weights.items():
        overall += indicators[key] * weight
    
    indicators["overall_harmony"] = min(100, max(0, int(overall)))
    
    return indicators


@lru_cache(maxsize=500)
def get_synastry_analysis(
    personA_birth_date: date,
    personA_birth_time: str,
    personA_birth_city: str,
    personB_birth_date: date,
    personB_birth_time: str,
    personB_birth_city: str,
    include_composite: bool = True,
    include_indicators: bool = True
) -> Dict[str, Any]:
    """
    获取完整的合盘分析数据

    :param personA_birth_date: A 的出生日期
    :param personA_birth_time: A 的出生时间
    :param personA_birth_city: A 的出生城市
    :param personB_birth_date: B 的出生日期
    :param personB_birth_time: B 的出生时间
    :param personB_birth_city: B 的出生城市
    :param include_composite: 是否包含组合盘
    :param include_indicators: 是否包含关系指标
    :return: 完整的合盘分析数据
    """
    # 获取两人的本命盘
    chart_a = get_natal_chart(personA_birth_date, personA_birth_time, personA_birth_city)
    chart_b = get_natal_chart(personB_birth_date, personB_birth_time, personB_birth_city)
    
    # 计算比较盘
    synastry = calculate_synastry(chart_a, chart_b)
    
    result = {
        "personA_chart": chart_a,
        "personB_chart": chart_b,
        "synastry": synastry
    }
    
    # 可选：计算组合盘
    if include_composite:
        composite = calculate_composite(chart_a, chart_b)
        result["composite"] = composite
    
    # 可选：计算关系指标
    if include_indicators:
        indicators = calculate_relationship_indicators(synastry, result.get("composite", {}))
        result["relationship_indicators"] = indicators
    
    return result
