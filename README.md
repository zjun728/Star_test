# 星盘查询 API 服务

基于用户输入的**日期**与**城市**（如广州），计算当日星盘数据，供星座运势分析使用。  
适用于在**扣子（Coze）**等智能体平台的工作流中，通过 HTTP 调用本服务获取星盘数据。

## 功能

- **当日星盘**：指定日期、城市（及可选时刻），返回当日行星位置、上升/天顶、月相等。
- **本命盘**：指定出生日期、出生时间、出生地城市，返回本命盘数据。
- **支持城市**：广州、北京、上海、深圳、杭州、成都、武汉、西安、南京、重庆、天津、苏州、长沙、郑州、沈阳、青岛、香港、台北等（见 `/api/cities`）。

## 安装与运行

### 1. 创建虚拟环境（推荐）

```bash
cd star_cursor
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python main.py
```

或指定端口：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

服务默认地址：`http://127.0.0.1:8000`  
API 文档：`http://127.0.0.1:8000/docs`

## API 说明

### 健康检查

- **GET /**  
  返回服务说明与可用接口列表。

### 支持的城市列表

- **GET /api/cities**  
  返回所有支持的城市名称列表，便于工作流或前端选择。

### 当日星盘（推荐在工作流中调用）

- **GET /api/daily-chart**  
  - 参数：`date`（可选，YYYY-MM-DD，默认今天）、`city`（必填，如「广州」）、`time`（可选，HH:MM，默认 12:00）  
  - 示例：`GET /api/daily-chart?city=广州` 或 `GET /api/daily-chart?date=2025-03-02&city=广州&time=12:00`

- **POST /api/daily-chart**  
  - Body (JSON)：`{"date": "2025-03-02", "city": "广州", "time": "12:00"}`  
  - `date`、`time` 可选，不传则使用当天、中午 12:00。

### 本命盘

- **POST /api/natal-chart**  
  - Body (JSON)：`{"birth_date": "1990-05-20", "birth_time": "14:30", "city": "广州"}`

### 响应格式

成功时返回：

```json
{
  "success": true,
  "data": {
    "date": "2025-03-02",
    "city": "广州",
    "location": { "lat": 23.1291, "lon": 113.2644, "timezone": "UTC+08:00" },
    "planets": [
      {
        "id": "Sun",
        "name_cn": "太阳",
        "name_en": "Sun",
        "sign": "Pisces",
        "sign_lon": 11.234,
        "longitude": 341.234,
        "latitude": 0.0,
        "speed": 0.9856,
        "movement": "Direct"
      }
    ],
    "angles": [
      { "id": "Asc", "name_cn": "上升点", "name_en": "Ascendant", "sign": "Virgo", "sign_lon": 5.2, "longitude": 155.2 }
    ],
    "moon_phase": "Waxing Crescent",
    "is_diurnal": true
  }
}
```

## 在扣子（Coze）工作流中使用

1. 将本服务部署到可公网访问的地址（如云服务器 + Nginx，或内网穿透）。
2. 在工作流中添加「HTTP 请求」节点：
   - 方法：GET 或 POST
   - URL：`https://你的域名/api/daily-chart`
   - GET 时在 Query 中设置 `city`、可选 `date`、`time`；POST 时在 Body 中传 JSON。
3. 将返回的 `data`（或其中的 `planets`、`angles`、`moon_phase`）作为后续节点的输入，用于生成星座运势分析文案。

## 技术栈

- **Python 3**
- **FastAPI**：HTTP API
- **flatlib**：占星盘计算（行星位置、宫位、月相等）

## 部署到 Render

1. 将本仓库推送到 GitHub（或 GitLab），或上传源码压缩包后通过 Render 连接仓库。
2. 登录 [Render](https://render.com/) → **Dashboard** → **New** → **Web Service**。
3. 连接你的仓库，选择 `star_cursor` 项目所在仓库。
4. 配置：
   - **Name**: `star-chart-api`（或任意名称）
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. 点击 **Create Web Service**，等待构建与部署完成。
6. 部署成功后，Render 会分配一个 URL，例如 `https://star-chart-api-xxxx.onrender.com`。  
   - 当日星盘：`GET https://你的服务URL/api/daily-chart?city=广州`  
   - API 文档：`https://你的服务URL/docs`

若使用 **Blueprint** 一键部署，在仓库根目录保留 `render.yaml`，在 Render 中选择 **New** → **Blueprint**，连接仓库后即可按 `render.yaml` 自动创建 Web Service。

## 扩展

- 增加城市：在 `config.py` 的 `CITIES` 中追加 `"城市名": (纬度, 经度, 时区小时)`。
- 若需更高精度星历，可考虑改用基于 Swiss Ephemeris 的 `pyswisseph` 替代 flatlib（需额外安装与数据文件）。
