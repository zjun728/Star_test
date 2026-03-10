# -*- coding: utf-8 -*-
"""
合盘分析 API 接口
提供比较盘和组合盘的查询功能
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from synastry_service import get_synastry_analysis


def parse_birth_date(date_str: str) -> date:
    """解析出生日期"""
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式错误，请使用 YYYY-MM-DD 格式"
        )


def validate_birth_time(time_str: str) -> None:
    """验证出生时间格式"""
    if ":" not in time_str:
        raise HTTPException(
            status_code=400,
            detail="时间格式错误，请使用 HH:MM 格式（如 14:30）"
        )


def handle_error(e: Exception) -> None:
    """统一错误处理"""
    error_msg = str(e)
    if "暂不支持城市" in error_msg:
        raise HTTPException(
            status_code=400,
            detail=f"城市错误：{error_msg}"
        )
    elif hasattr(e, 'status_code') and e.status_code == 400:  # type: ignore
        raise
    else:
        # 其他错误返回 500
        raise HTTPException(
            status_code=500,
            detail=f"合盘计算失败：{error_msg}"
        )


class PersonInfo(BaseModel):
    """个人信息模型"""
    name: str = Field(..., description="姓名", example="张三")
    birth_date: str = Field(..., description="出生日期（YYYY-MM-DD）", example="1990-05-15")
    birth_time: str = Field(..., description="出生时间（HH:MM）", example="14:30")
    birth_city: str = Field(..., description="出生城市", example="广州")
    current_city: Optional[str] = Field(None, description="现居住城市（可选）", example="北京")


class SynastryQuery(BaseModel):
    """合盘查询请求模型"""
    personA: PersonInfo = Field(..., description="甲方信息")
    personB: PersonInfo = Field(..., description="乙方信息")
    include_composite: bool = Field(True, description="是否包含组合盘数据")
    include_indicators: bool = Field(True, description="是否包含关系指标评分")


router = APIRouter(prefix="/api", tags=["合盘分析"])


@router.post("/synastry-chart")
async def get_synastry_chart(body: SynastryQuery):
    """
    获取合盘分析数据（比较盘 + 组合盘）
    
    **功能说明：**
    
    1. **比较盘（Synastry）** - 分析两人星盘的相互作用
       - A 的行星落入 B 的宫位
       - B 的行星落入 A 的宫位
       - 两人行星之间的交叉相位
    
    2. **组合盘（Composite Chart）** - 两人的关系星盘
       - 基于两人行星中点计算
       - 反映关系的本质和发展方向
    
    3. **关系指标** - 关键维度的评分
       - 情感兼容性
       - 沟通分数
       - 身体吸引力
       - 长期潜力
       - 整体和谐度
    
    **使用场景：**
    
    - 情侣合盘分析
    - 夫妻婚姻匹配
    - 商业伙伴关系
    - 朋友关系分析
    - 亲子关系分析
    
    **返回数据说明：**
    
    ```json
    {
      "success": true,
      "data": {
        "personA_chart": {...},      // A 的本命盘
        "personB_chart": {...},      // B 的本命盘
        "synastry": {                // 比较盘
          "planets_in_houses": [...],  // 行星落入宫位
          "cross_aspects": [...]       // 交叉相位
        },
        "composite": {...},          // 组合盘（可选）
        "relationship_indicators": { // 关系指标（可选）
          "emotional_compatibility": 85,
          "communication_score": 72,
          "physical_attraction": 90,
          "long_term_potential": 78,
          "overall_harmony": 80
        }
      }
    }
    ```
    
    **大模型分析建议：**
    
    将返回数据交给大模型，可以从以下维度分析：
    
    1. **情感契合度** - 日月金月的相位
    2. **沟通模式** - 水星相关相位
    3. **性吸引力** - 火星、金星、8 宫的互动
    4. **长期稳定性** - 土星、月亮的相位
    5. **成长潜力** - 木星的影响
    6. **挑战与功课** - 困难相位的意义
    """
    try:
        # 解析日期
        birth_date_a = parse_birth_date(body.personA.birth_date)
        birth_date_b = parse_birth_date(body.personB.birth_date)
        
        # 验证出生时间格式
        validate_birth_time(body.personA.birth_time)
        validate_birth_time(body.personB.birth_time)
        
        # 获取合盘数据
        result = get_synastry_analysis(
            personA_birth_date=birth_date_a,
            personA_birth_time=body.personA.birth_time,
            personA_birth_city=body.personA.birth_city,
            personB_birth_date=birth_date_b,
            personB_birth_time=body.personB.birth_time,
            personB_birth_city=body.personB.birth_city,
            include_composite=body.include_composite,
            include_indicators=body.include_indicators
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        handle_error(e)


@router.post("/relationship-compatibility")
async def get_relationship_compatibility(body: SynastryQuery):
    """
    简化版关系兼容性分析
    
    只返回关键指标，不包含完整数据
    适合快速评估两人关系的兼容性
    """
    try:
        # 解析日期
        birth_date_a = parse_birth_date(body.personA.birth_date)
        birth_date_b = parse_birth_date(body.personB.birth_date)
        
        # 验证出生时间格式
        validate_birth_time(body.personA.birth_time)
        validate_birth_time(body.personB.birth_time)
        
        # 获取完整数据
        result = get_synastry_analysis(
            personA_birth_date=birth_date_a,
            personA_birth_time=body.personA.birth_time,
            personA_birth_city=body.personA.birth_city,
            personB_birth_date=birth_date_b,
            personB_birth_time=body.personB.birth_time,
            personB_birth_city=body.personB.birth_city,
            include_composite=True,
            include_indicators=True
        )
        
        # 只返回关键信息
        simplified = {
            "overall_harmony": result["relationship_indicators"]["overall_harmony"],
            "key_strengths": [],
            "key_challenges": [],
            "top_aspects": result["synastry"]["cross_aspects"][:5],  # 前 5 个重要相位
            "summary": f"整体和谐度：{result['relationship_indicators']['overall_harmony']}/100"
        }
        
        # 提取关键优势
        for entry in result["synastry"]["planets_in_houses"]:
            if entry["house_number"] in [5, 7] and entry["planet_name"] in ["太阳", "月亮", "金星"]:
                simplified["key_strengths"].append(entry["description"])
        
        # 提取关键挑战（困难相位）
        for aspect in result["synastry"]["cross_aspects"]:
            if aspect["aspect_name_cn"] in ["四分相", "对分相"]:
                simplified["key_challenges"].append(aspect["description"])
        
        return {
            "success": True,
            "data": simplified
        }
        
    except Exception as e:
        handle_error(e)
