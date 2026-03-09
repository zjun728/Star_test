# 星盘 API 接口数据结构完整说明

基于实际测试结果整理的所有接口返回数据结构

---

## 📋 接口总览

| 序号 | 接口 | 方法 | 功能 |
|------|------|------|------|
| 1 | `/` | GET | 根路径 - 服务信息 |
| 2 | `/api/cities` | GET | 城市列表查询 |
| 3 | `/api/daily-chart` | GET/POST | 当日星盘查询 |
| 4 | `/api/natal-chart` | POST | 本命盘查询 |
| 5 | `/api/daily-aspects` | POST | 当日相位查询 |

---

## 1️⃣ 根路径 - GET /

**请求：** `GET https://star-test.onrender.com/`

**响应数据结构：**
```json
{
  "service": "星盘查询 API",
  "docs": "/docs",
  "endpoints": {
    "daily_chart": "GET/POST /api/daily-chart - 当日星盘",
    "natal_chart": "POST /api/natal-chart - 本命盘",
    "cities": "GET /api/cities - 支持的城市列表"
  }
}
```

---

## 2️⃣ 城市列表 - GET /api/cities

**请求：** `GET https://star-test.onrender.com/api/cities?q=广州&limit=5`

**参数说明：**
- `q` (可选): 搜索关键字，如「广」「广州」
- `limit` (可选): 最多返回数量，默认 200，最大 1000

**响应数据结构：**
```json
{
  "cities": [
    {
      "name": "广州",
      "short": "广州",
      "province": ""
    }
  ],
  "count": 1
}
```

---

## 3️⃣ 当日星盘 - GET/POST /api/daily-chart

### GET 请求示例
**请求：** `GET https://star-test.onrender.com/api/daily-chart?date=2025-03-05&city=广州&time=12:00`

**参数说明：**
- `date` (可选): 日期 YYYY-MM-DD，默认今天
- `city` (必填): 城市名称，如「广州」
- `time` (可选): 时间 HH:MM，默认 12:00

### POST 请求示例
**请求：** `POST https://star-test.onrender.com/api/daily-chart`

**请求体：**
```json
{
  "date": "2025-03-05",
  "city": "广州",
  "time": "12:00"
}
```

### 响应数据结构（重点⭐）
```json
{
  "success": true,
  "data": {
    "date": "2026-03-05",                    // 查询日期
    "city": "广州",                           // 城市
    "location": {
      "lat": 23.13,                          // 纬度
      "lon": 113.27,                         // 经度
      "timezone": "UTC+08:00"                // 时区
    },
    "planets": [                             // 行星列表（11 个天体）
      {
        "id": "Sun",                         // 行星 ID（flatlib 常量）
        "name_cn": "太阳",                   // 中文名
        "name_en": "Sun",                    // 英文名
        "sign": "Pisces",                    // 星座（英文）
        "sign_lon": 14.5835,                 // 星座内度数（0-30）
        "longitude": 344.5835,               // 黄道经度（0-360）
        "latitude": -0.000081,               // 黄道纬度
        "speed": 1.001538,                   // 运行速度（度/天）
        "movement": "Direct"                 // 运动状态：顺行/逆行
      }
      // ... 其他 10 个行星：月亮、水星、金星、火星、木星、土星、天王星、海王星、冥王星、北交点、南交点、朔望点、福点
    ],
    "angles": [                              // 角度点（上升点、天顶）
      {
        "id": "Asc",                         // Asc=上升点，MC=天顶
        "name_cn": "上升点",
        "name_en": "Ascendant",
        "sign": "Gemini",
        "sign_lon": 17.6422,
        "longitude": 77.6422
      },
      {
        "id": "MC",
        "name_cn": "天顶",
        "name_en": "MC",
        "sign": "Pisces",
        "sign_lon": 4.3178,
        "longitude": 334.3178
      }
    ],
    "moon_phase": "Third Quarter",           // 月相
    "is_diurnal": true                       // 是否日间出生（日出后日落前）
  }
}
```

**行星列表完整数据（11 个）：**
1. Sun (太阳)
2. Moon (月亮)
3. Mercury (水星)
4. Venus (金星)
5. Mars (火星)
6. Jupiter (木星)
7. Saturn (土星)
8. North Node (北交点)
9. South Node (南交点)
10. Syzygy (朔望点)
11. Pars Fortuna (福点)

---

## 4️⃣ 本命盘 - POST /api/natal-chart

**请求：** `POST https://star-test.onrender.com/api/natal-chart`

**请求体：**
```json
{
  "birth_date": "1990-05-20",
  "birth_time": "14:30",
  "city": "广州"
}
```

**参数说明：**
- `birth_date` (必填): 出生日期 YYYY-MM-DD
- `birth_time` (必填): 出生时间 HH:MM
- `city` (必填): 出生地城市

### 响应数据结构
```json
{
  "success": true,
  "data": {
    "date": "1990-05-20",                    // 出生日期
    "city": "广州",                           // 出生地
    "location": {
      "lat": 23.13,
      "lon": 113.27,
      "timezone": "UTC+08:00"
    },
    "planets": [                             // 行星列表（同当日星盘）
      {
        "id": "Sun",
        "name_cn": "太阳",
        "name_en": "Sun",
        "sign": "Taurus",                    // 金牛座
        "sign_lon": 28.99,
        "longitude": 58.99,
        "latitude": 0.0,
        "speed": 0.9856,
        "movement": "Direct"
      }
      // ... 其他行星
    ],
    "angles": [                              // 角度点
      {"id": "Asc", "name_cn": "上升点", ...},
      {"id": "MC", "name_cn": "天顶", ...}
    ],
    "moon_phase": "Waning Crescent",         // 出生时月相
    "is_diurnal": true,                      // 是否日间出生
    "summary": {                             // ⭐ 本命盘特有字段
      "sun_sign_en": "Taurus",               // 太阳星座（英文）
      "sun_sign_cn": "金牛座"                 // 太阳星座（中文）
    }
  }
}
```

---

## 5️⃣ 当日相位 - POST /api/daily-aspects

**请求：** `POST https://star-test.onrender.com/api/daily-aspects`

**请求体：**
```json
{
  "date": "2025-03-05",
  "city": "广州",
  "time": "12:00"
}
```

### 响应数据结构
```json
{
  "success": true,
  "data": {
    "date": "2025-03-05",
    "city": "广州",
    "location": {
      "lat": 23.13,
      "lon": 113.27,
      "timezone": "UTC+08:00"
    },
    "aspects": [                             // 相位列表（22 个相位）
      {
        "object1": {                         // 第一颗行星
          "id": "Sun",
          "name_cn": "太阳",
          "name_en": "Sun",
          "sign": "Pisces",
          "sign_lon": 14.58
        },
        "object2": {                         // 第二颗行星
          "id": "Moon",
          "name_cn": "月亮",
          "name_en": "Moon",
          "sign": "Taurus",
          "sign_lon": 24.72
        },
        "aspect": {                          // 相位信息
          "type_angle": "sextile",           // 相位类型（flatlib 常量）
          "type_cn": "六合",                 // 相位中文名
          "type_en": "Sextile",              // 相位英文名
          "orb": 10.14,                      // 容许度（精确度数差）
          "movement": "Applying",            // 相位状态：Applying(入相) / Separating(出相)
          "direction": "Left",               // 方向
          "condition": "Good",               // 条件
          "active_id": "Sun",                // 主动行星 ID
          "passive_id": "Moon",              // 被动行星 ID
          "mutual_in_orb": true              // 是否互在容许度内
        }
      }
      // ... 其他 21 个相位
    ]
  }
}
```

**主要相位类型：**
1. 合相 (Conjunction) - 0°
2. 六分相/六合 (Sextile) - 60° ✨ 吉相
3. 四分相/刑 (Square) - 90° ⚠️ 凶相
4. 三分相/拱 (Trine) - 120° ✨ 吉相
5. 对分相/冲 (Opposition) - 180° ⚠️ 凶相

---

## 🎯 关键发现与设计建议

### 现有数据结构特点：

1. **行星数据完整**：包含 11 个天体的精确位置、速度、运动状态
2. **相位分析详细**：包含 22 个相位，有容许度、主被动关系等
3. **基础信息齐全**：经纬度、时区、月相、昼夜

### 新增运势接口的数据基础：

✅ **可直接使用的字段：**
- `planets[].sign` - 星座位置 → 判断行星落入哪个宫位
- `planets[].sign_lon` - 星座度数 → 计算相位精确度
- `moon_phase` - 月相 → 情感运势指标
- `aspects[]` - 相位列表 → 吉凶事件预测

### 推荐的运势接口设计：

```python
# 新增接口结构
GET /api/horoscope/weekly   # 周运势
GET /api/horoscope/monthly  # 月运势  
GET /api/horoscope/yearly   # 年运势

# 请求参数
{
    "sign": "Aries",              # 星座（必填）
    "start_date": "2025-03-10",   # 开始日期（可选）
    "end_date": "2025-03-16",     # 结束日期（可选）
    "city": "广州"                 # 参考城市（可选）
}

# 响应结构建议
{
    "success": true,
    "data": {
        "sign": "Aries",
        "period_type": "weekly",
        "start_date": "2025-03-10",
        "end_date": "2025-03-16",
        
        # 综合评分（1-10 分）
        "scores": {
            "overall": 7.5,        # 整体运势
            "love": 8.0,           # 爱情运
            "career": 6.5,         # 事业运
            "wealth": 7.0,         # 财富运
            "health": 8.5          # 健康运
        },
        
        # 关键星象事件
        "key_events": [
            {
                "date": "2025-03-12",
                "type": "transit",
                "description": "金星进入白羊座，提升魅力指数",
                "impact": "positive"
            },
            {
                "date": "2025-03-14",
                "type": "aspect",
                "description": "火星与土星形成四分相，注意冲动决策",
                "impact": "challenging"
            }
        ],
        
        # 每日亮点（周/月运势）
        "daily_highlights": [
            {
                "date": "2025-03-10",
                "lucky_score": 8,
                "highlight": "适合开启新项目"
            }
        ],
        
        # 运势解读
        "summary": "本周白羊座整体运势上扬，尤其是爱情和社交方面...",
        "advice": "把握前半周的好运，周四周五谨慎行事..."
    }
}
```

---

## 📝 实现步骤建议

### 第一阶段：基础框架
1. 新增运势相关的路由文件 `horoscope_router.py`
2. 定义请求/响应模型
3. 实现时间段星盘计算工具

### 第二阶段：核心算法
1. 实现星座守护星分析逻辑
2. 实现行星换座检测
3. 实现重要相位筛选
4. 实现吉凶评分系统

### 第三阶段：文案生成
1. 创建运势解读模板库
2. 基于评分匹配对应文案
3. 或接入 AI 动态生成

---

**测试时间：** 2026-03-05  
**API 版本：** v1.0.0  
**服务地址：** https://star-test.onrender.com
