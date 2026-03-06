# -*- coding: utf-8 -*-
"""测试星盘 API 的所有接口"""

import requests
import json

BASE_URL = "https://star-test.onrender.com"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_root():
    """测试根路径"""
    print_section("1. 根路径 - GET /")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=30)
        print(f"状态码：{response.status_code}")
        print(f"响应数据:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"请求失败：{e}")

def test_cities():
    """测试城市列表"""
    print_section("2. 城市列表 - GET /api/cities")
    try:
        # 获取前 5 个城市
        print("获取前 5 个城市:")
        response = requests.get(f"{BASE_URL}/api/cities?limit=5", timeout=30)
        print(f"状态码：{response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        # 搜索广州
        print("\n\n搜索「广州」:")
        response = requests.get(f"{BASE_URL}/api/cities?q=广州", timeout=30)
        print(f"状态码：{response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"请求失败：{e}")

def test_daily_chart_get():
    """测试当日星盘 GET"""
    print_section("3. 当日星盘 (GET) - GET /api/daily-chart")
    try:
        params = {
            "date": "2025-03-05",
            "city": "广州",
            "time": "12:00"
        }
        response = requests.get(f"{BASE_URL}/api/daily-chart", params=params, timeout=30)
        print(f"状态码：{response.status_code}")
        print(f"请求参数：{params}")
        print(f"响应数据:")
        data = response.json()
        if data.get("success"):
            result = data["data"]
            print(f"日期：{result['date']}")
            print(f"城市：{result['city']}")
            print(f"位置：{result['location']}")
            print(f"\n行星数量：{len(result['planets'])}")
            print("第一个行星（太阳）数据:")
            for planet in result['planets']:
                if planet['id'] == 'Sun':
                    print(json.dumps(planet, indent=2, ensure_ascii=False))
                    break
            
            print(f"\n角度点数量：{len(result['angles'])}")
            print("角度点数据:")
            print(json.dumps(result['angles'], indent=2, ensure_ascii=False))
            
            print(f"\n月相：{result['moon_phase']}")
            print(f"是否日间：{result['is_diurnal']}")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"请求失败：{e}")

def test_daily_chart_post():
    """测试当日星盘 POST"""
    print_section("4. 当日星盘 (POST) - POST /api/daily-chart")
    try:
        payload = {
            "date": "2025-03-05",
            "city": "广州",
            "time": "12:00"
        }
        response = requests.post(f"{BASE_URL}/api/daily-chart", json=payload, timeout=30)
        print(f"状态码：{response.status_code}")
        print(f"请求体：{payload}")
        print(f"响应数据:")
        data = response.json()
        if data.get("success"):
            result = data["data"]
            print(f"行星总数：{len(result['planets'])}")
            print("所有行星列表:")
            for planet in result['planets']:
                print(f"  - {planet['name_cn']} ({planet['id']}): {planet['sign']} {planet['sign_lon']:.2f}°")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"请求失败：{e}")

def test_natal_chart():
    """测试本命盘"""
    print_section("5. 本命盘 - POST /api/natal-chart")
    try:
        payload = {
            "birth_date": "1990-05-20",
            "birth_time": "14:30",
            "city": "广州"
        }
        response = requests.post(f"{BASE_URL}/api/natal-chart", json=payload, timeout=30)
        print(f"状态码：{response.status_code}")
        print(f"请求体：{payload}")
        print(f"响应数据:")
        data = response.json()
        if data.get("success"):
            result = data["data"]
            print(f"出生日期：{result['date']}")
            print(f"出生地：{result['city']}")
            print(f"\n总结信息：{result.get('summary', {})}")
            print(f"\n行星总数：{len(result['planets'])}")
            print("主要行星:")
            for planet in result['planets'][:5]:
                print(f"  - {planet['name_cn']}: {planet['sign']} ({planet['sign_lon']:.2f}°)")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"请求失败：{e}")

def test_daily_aspects():
    """测试当日相位"""
    print_section("6. 当日相位 - POST /api/daily-aspects")
    try:
        payload = {
            "date": "2025-03-05",
            "city": "广州",
            "time": "12:00"
        }
        response = requests.post(f"{BASE_URL}/api/daily-aspects", json=payload, timeout=30)
        print(f"状态码：{response.status_code}")
        print(f"请求体：{payload}")
        print(f"响应数据:")
        data = response.json()
        if data.get("success"):
            result = data["data"]
            print(f"日期：{result['date']}")
            print(f"城市：{result['city']}")
            print(f"\n相位总数：{len(result['aspects'])}")
            print("前 5 个相位:")
            for aspect in result['aspects'][:5]:
                obj1 = aspect['object1']['name_cn']
                obj2 = aspect['object2']['name_cn']
                asp_type = aspect['aspect']['type_cn']
                orb = aspect['aspect']['orb']
                print(f"  - {obj1} {asp_type} {obj2} (容许度：{orb:.2f}°)")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"请求失败：{e}")

if __name__ == "__main__":
    print("="*60)
    print("  星盘 API 接口测试")
    print("="*60)
    
    test_root()
    test_cities()
    test_daily_chart_get()
    test_daily_chart_post()
    test_natal_chart()
    test_daily_aspects()
    
    print("\n\n所有接口测试完成！\n")
