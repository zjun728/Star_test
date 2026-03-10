# -*- coding: utf-8 -*-
"""城市经纬度与时区配置，支持全国城市与搜索。

依赖项目根目录下的 china_cities.json，结构示例：
{
  "cities": [
    {
      "name": "广州市",
      "short": "广州",
      "province": "广东省",
      "lat": 23.1291,
      "lon": 113.2644,
      "tz": 8,
      "aliases": ["广州", "广州市"]
    }
  ]
}
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR
CHINA_CITIES_FILE = PROJECT_ROOT / "china_cities.json"


def _normalize_city_name(name: str) -> str:
    """归一化城市名：去空格、去掉「市」，统一小写。"""
    n = (name or "").strip()
    if not n:
        return ""
    if n.endswith("市"):
        n = n[:-1]
    return n.lower()


@lru_cache
def _load_cities() -> List[Dict[str, Any]]:
    """从 china_cities.json 加载城市数据。"""
    if not CHINA_CITIES_FILE.exists():
        return []

    with CHINA_CITIES_FILE.open("r", encoding="utf-8") as f:
        raw = f.read()

    # 兼容可能存在的尾逗号等小问题
    raw_stripped = raw.rstrip()
    if raw_stripped.endswith(",}"):
        raw_stripped = raw_stripped[:-2] + "}"

    try:
        data = json.loads(raw_stripped)
    except json.JSONDecodeError:
        data = json.loads(raw)

    if isinstance(data, dict) and "cities" in data:
        cities = data["cities"]
    elif isinstance(data, list):
        cities = data
    else:
        cities = []

    normalized: List[Dict[str, Any]] = []
    for c in cities:
        if not isinstance(c, dict):
            continue
        name = c.get("name")
        short = c.get("short") or name
        if not name:
            continue

        try:
            lat = float(c.get("lat"))
            lon = float(c.get("lon"))
        except (TypeError, ValueError):
            continue

        tz = int(c.get("tz", 8))

        normalized.append(
            {
                "name": name,
                "short": short,
                "province": c.get("province") or "",
                "lat": lat,
                "lon": lon,
                "tz": tz,
                "aliases": c.get("aliases") or [],
            }
        )

    return normalized


@lru_cache
def _build_city_index() -> Dict[str, Dict[str, Any]]:
    """基于 name / short / aliases 构建索引，便于快速查找城市。"""
    index: Dict[str, Dict[str, Any]] = {}
    for c in _load_cities():
        keys = [c["name"], c["short"], *c.get("aliases", [])]
        for k in keys:
            nk = _normalize_city_name(k)
            if not nk:
                continue
            index.setdefault(nk, c)
    return index


def get_city_coords(city: str):
    """
    根据城市名称返回 (纬度, 经度, 时区小时)。
    支持「广州」「广州市」「Guangzhou」等写法。
    若城市不在表中，返回 None。
    """
    if not city or not isinstance(city, str):
        return None
    key = _normalize_city_name(city)
    if not key or len(key) < 2:
        return None
    info = _build_city_index().get(key)
    if not info:
        return None
    return info["lat"], info["lon"], info["tz"]


def search_cities(keyword: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    """
    搜索城市列表，用于 /api/cities。

    :param keyword: 可选关键字，如「广」「广州」「guangzhou」等
    :param limit: 最多返回条数
    """
    cities = _load_cities()
    if not keyword:
        return cities[:limit]

    kw = keyword.strip()
    if not kw:
        return cities[:limit]

    kw_lower = kw.lower()
    result: List[Dict[str, Any]] = []

    for c in cities:
        candidates = [c["name"], c["short"], c.get("province", "")]
        candidates.extend(c.get("aliases", []))
        text = " ".join(map(str, candidates))
        if kw in text or kw_lower in text.lower():
            result.append(c)
            if len(result) >= limit:
                break

    return result
