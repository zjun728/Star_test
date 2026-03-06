# -*- coding: utf-8 -*-
"""
星盘数据查询接口（带内存缓存）
提供周、月、年的星盘抽样数据查询
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Tuple
from calendar import monthrange
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chart_service import get_daily_chart
from config import get_city_coords

router = APIRouter(prefix="/api", tags=["星盘数据查询"])


# ========== Pydantic 请求模型 ==========

class DateCityQuery(BaseModel):
    """日期 + 城市查询基础模型"""
    date: str = Field(None, description="查询日期 YYYY-MM-DD，默认今天")
    city: str = Field(..., description="城市名称，如：广州")


# ========== 工具函数 ==========

def _get_week_sampling_dates(base_date: date) -> List[Tuple[date, str]]:
    """
    获取一周的抽样日期（周一、周三、周五）
    """
    weekday = base_date.weekday()
    monday = base_date - timedelta(days=weekday)
    
    sampling_days = [0, 2, 4]
    week_names = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                  "Friday", "Saturday", "Sunday"]
    
    return [
        (monday + timedelta(days=day), week_names[day])
        for day in sampling_days
    ]


def _get_month_sampling_dates(year: int, month: int) -> List[Tuple[date, str]]:
    """
    获取一个月的抽样日期（自动适配闰年/平年）
    """
    _, days_in_month = monthrange(year, month)
    
    sample_days = [1, 8, 15, 22]
    phase_labels = ["月初", "第一周结束", "月中", "第三周结束"]
    
    samples = []
    for day, label in zip(sample_days, phase_labels):
        samples.append((date(year, month, day), label))
    
    last_day = date(year, month, days_in_month)
    samples.append((last_day, "月末"))
    
    return samples


def _get_year_sampling_dates(year: int) -> List[Tuple[int, date]]:
    """获取一年的抽样日期（每月 15 日）"""
    samples = []
    for month in range(1, 13):
        sample_date = date(year, month, 15)
        samples.append((month, sample_date))
    return samples


@lru_cache(maxsize=1000)
def _get_cached_chart(date_str: str, city: str) -> Dict[str, Any]:
    """
    获取缓存的星盘数据（内存缓存）
    
    cache key: (date_str, city)
    maxsize: 1000 条记录
    """
    try:
        chart_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")
    
    chart = get_daily_chart(chart_date, city, "12:00")
    
    return {
        "date": chart_date.isoformat(),
        "planets": chart["planets"],
        "angles": chart["angles"],
        "moon_phase": chart["moon_phase"],
        "is_diurnal": chart["is_diurnal"]
    }


def _build_chart_data(chart_date: date, city: str, is_today: bool = False) -> Dict[str, Any]:
    """构建单个日期的星盘数据（使用缓存）"""
    date_str = chart_date.isoformat()
    chart_data = _get_cached_chart(date_str, city)
    chart_data["is_today"] = is_today
    return chart_data


# ========== POST 接口 ==========

@router.post("/weekly-chart")
async def get_weekly_chart(body: DateCityQuery):
    """
    获取周星盘抽样数据（POST）
    
    自动根据查询日期推算所属周，抽取周一、三、五的星盘数据
    使用内存缓存提升性能
    """
    if body.date and body.date.strip():
        try:
            query_date = date.fromisoformat(body.date.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")
    else:
        query_date = date.today()
    
    city = body.city.strip()
    sampling_dates = _get_week_sampling_dates(query_date)
    
    sampled_charts = []
    for sample_date, weekday_name in sampling_dates:
        is_today = (sample_date == query_date)
        chart_data = _build_chart_data(sample_date, city, is_today)
        chart_data["weekday"] = weekday_name
        sampled_charts.append(chart_data)
    
    weekday = query_date.weekday()
    monday = query_date - timedelta(days=weekday)
    sunday = monday + timedelta(days=6)
    
    week_names = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                  "Friday", "Saturday", "Sunday"]
    
    return {
        "success": True,
        "data": {
            "query_date": query_date.isoformat(),
            "weekday": week_names[weekday],
            "week_range": {
                "start": monday.isoformat(),
                "end": sunday.isoformat()
            },
            "sampling_strategy": "周一、周三、周五（3 个采样点）",
            "sampled_charts": sampled_charts
        }
    }


@router.post("/monthly-chart")
async def get_monthly_chart(body: DateCityQuery):
    """
    获取月星盘抽样数据（POST）
    
    自动根据查询日期推算所属月，抽取 5 个采样点
    （已考虑闰年/平年，2 月自动使用 28/29 日）
    使用内存缓存提升性能
    """
    if body.date and body.date.strip():
        try:
            query_date = date.fromisoformat(body.date.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误")
    else:
        query_date = date.today()
    
    city = body.city.strip()
    year = query_date.year
    month = query_date.month
    
    sampling_dates = _get_month_sampling_dates(year, month)
    
    sampled_charts = []
    for sample_date, phase_label in sampling_dates:
        is_today = (sample_date == query_date)
        chart_data = _build_chart_data(sample_date, city, is_today)
        chart_data["day_of_month"] = sample_date.day
        chart_data["phase_label"] = phase_label
        sampled_charts.append(chart_data)
    
    _, days_in_month = monthrange(year, month)
    is_leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    
    return {
        "success": True,
        "data": {
            "query_date": query_date.isoformat(),
            "month_range": {
                "year": year,
                "month": month,
                "days_in_month": days_in_month,
                "is_leap_year": is_leap_year
            },
            "sampling_strategy": "1 号、8 号、15 号、22 号、最后一天（5 个采样点）",
            "sampled_charts": sampled_charts
        }
    }


@router.post("/yearly-chart")
async def get_yearly_chart(body: DateCityQuery):
    """
    获取年星盘抽样数据（POST）
    
    自动根据查询日期推算所属年，抽取每月 15 日的星盘数据
    使用内存缓存提升性能
    """
    if body.date and body.date.strip():
        try:
            query_date = date.fromisoformat(body.date.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误")
    else:
        query_date = date.today()
    
    city = body.city.strip()
    year = query_date.year
    
    sampling_dates = _get_year_sampling_dates(year)
    
    monthly_charts = []
    current_month = query_date.month
    
    for month_num, sample_date in sampling_dates:
        is_current_month = (month_num == current_month)
        chart_data = _build_chart_data(sample_date, city, is_today=is_current_month)
        chart_data["month"] = month_num
        chart_data["is_current_month"] = is_current_month
        monthly_charts.append(chart_data)
    
    return {
        "success": True,
        "data": {
            "query_date": query_date.isoformat(),
            "year": year,
            "sampling_strategy": "每月 15 日作为代表（12 个采样点）",
            "monthly_charts": monthly_charts
        }
    }


@router.post("/daily-chart-simple")
async def get_daily_chart_simple(body: DateCityQuery):
    """
    单日星盘查询（简化版 POST）
    
    返回某一天的完整星盘数据
    使用内存缓存提升性能
    
    与 /api/daily-chart 的区别：
    - 本接口只支持 POST，参数更简洁
    - /api/daily-chart 同时支持 GET 和 POST，功能更完整
    """
    if body.date and body.date.strip():
        try:
            query_date = date.fromisoformat(body.date.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误")
    else:
        query_date = date.today()
    
    city = body.city.strip()
    chart_data = _build_chart_data(query_date, city, is_today=True)
    
    return {
        "success": True,
        "data": chart_data
    }


@router.get("/cache-stats")
async def get_cache_stats():
    """
    获取缓存统计信息
    
    用于监控缓存使用情况
    """
    cache_info = _get_cached_chart.cache_info()
    
    hits = cache_info.hits
    misses = cache_info.misses
    total = hits + misses
    
    return {
        "success": True,
        "data": {
            "cache_hits": hits,
            "cache_misses": misses,
            "cache_size": cache_info.currsize,
            "cache_maxsize": cache_info.maxsize,
            "hit_rate": f"{hits / max(total, 1) * 100:.2f}%",
            "total_requests": total,
            "memory_estimate_kb": f"{cache_info.currsize * 5:.2f}"
        }
    }


@router.get("/cache-clear")
async def clear_cache():
    """
    清空缓存（GET）
    
    当需要强制刷新缓存时调用
    无需请求包体，直接访问即可
    """
    _get_cached_chart.cache_clear()
    
    return {
        "success": True,
        "message": "缓存已清空"
    }
