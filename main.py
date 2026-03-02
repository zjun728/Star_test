# -*- coding: utf-8 -*-
"""
星盘查询 API 服务。
供扣子/Coze 等工作流通过 HTTP 调用，获取当日星盘或本命盘数据。
支持部署到 Render 等云平台（使用环境变量 PORT）。
"""

import os
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field

from config import CITIES, get_city_coords
from chart_service import get_daily_chart, get_natal_chart

app = FastAPI(
    title="星盘查询 API",
    description="根据日期与城市查询当日星盘或本命盘数据，适用于扣子/Coze 等工作流调用。",
    version="1.0.0",
)


# ---------- 请求/响应模型 ----------


class DailyChartQuery(BaseModel):
    """当日星盘查询参数（POST body）。"""

    date: Optional[str] = Field(
        None,
        description="查询日期，YYYY-MM-DD，不传则默认为当天",
    )
    city: str = Field(..., description="城市名称，如：广州、北京、上海")
    time: Optional[str] = Field(
        "12:00",
        description="当天时刻 HH:MM，默认中午 12:00",
    )


class NatalChartQuery(BaseModel):
    """本命盘查询参数（POST body）。"""

    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    city: str = Field(..., description="出生地城市，如：广州")


# ---------- 接口 ----------


@app.get("/")
async def root():
    """健康检查与简要说明。"""
    return {
        "service": "星盘查询 API",
        "docs": "/docs",
        "endpoints": {
            "daily_chart": "GET/POST /api/daily-chart - 当日星盘",
            "natal_chart": "POST /api/natal-chart - 本命盘",
            "cities": "GET /api/cities - 支持的城市列表",
        },
    }


@app.get("/api/cities")
async def list_cities():
    """返回支持的城市列表，便于工作流或前端选择。"""
    return {
        "cities": sorted(CITIES.keys()),
        "count": len(CITIES),
    }


def _parse_date(s: Optional[str]) -> date:
    if not s or not s.strip():
        return date.today()
    try:
        return datetime.strptime(s.strip()[:10], "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误，请使用 YYYY-MM-DD: {e}")


@app.get("/api/daily-chart")
async def api_daily_chart_get(
    date_str: Optional[str] = Query(None, description="日期 YYYY-MM-DD，默认今天"),
    city: str = Query(..., description="城市名称，如：广州"),
    time: str = Query("12:00", description="时刻 HH:MM"),
):
    """
    查询当日星盘（GET）。
    扣子工作流可直接用 GET 请求，参数放在 query string。
    """
    chart_date = _parse_date(date_str)
    try:
        data = get_daily_chart(chart_date, city.strip(), time_str=time.strip() or "12:00")
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/daily-chart")
async def api_daily_chart_post(body: DailyChartQuery):
    """
    查询当日星盘（POST）。
    请求体示例: {"date": "2025-03-02", "city": "广州", "time": "12:00"}
    """
    chart_date = _parse_date(body.date)
    try:
        data = get_daily_chart(
            chart_date,
            body.city.strip(),
            time_str=(body.time or "12:00").strip(),
        )
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/natal-chart")
async def api_natal_chart(body: NatalChartQuery):
    """
    查询本命盘（出生时刻星盘）。
    请求体示例: {"birth_date": "1990-05-20", "birth_time": "14:30", "city": "广州"}
    """
    birth_date = _parse_date(body.birth_date)
    try:
        data = get_natal_chart(
            birth_date,
            body.birth_time.strip(),
            body.city.strip(),
        )
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
