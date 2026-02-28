"""
星盘计算API服务 - 基于Kerykeion
部署到Render/PythonAnywhere等云平台
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from kerykeion import AstrologicalSubject
import json
import traceback

app = Flask(__name__)
CORS(app)  # 允许跨域请求

class BirthChartCalculator:
    """星盘计算器 - 封装Kerykeion功能"""
    
    def __init__(self, name, birth_year, birth_month, birth_day, 
                 birth_hour, birth_minute, city, nation, 
                 lng=None, lat=None, tz_str=None):
        """
        初始化出生信息
        """
        self.name = name
        self.birth_year = int(birth_year)
        self.birth_month = int(birth_month)
        self.birth_day = int(birth_day)
        self.birth_hour = int(birth_hour)
        self.birth_minute = int(birth_minute)
        self.city = city
        self.nation = nation
        
        try:
            # 创建AstrologicalSubject实例
            if lng and lat and tz_str:
                # 直接使用经纬度
                self.subject = AstrologicalSubject(
                    name, self.birth_year, self.birth_month, self.birth_day,
                    self.birth_hour, self.birth_minute, 
                    lng=float(lng), lat=float(lat), tz_str=tz_str
                )
            else:
                # 使用城市+国家（自动查询GeoNames）
                self.subject = AstrologicalSubject(
                    name, self.birth_year, self.birth_month, self.birth_day,
                    self.birth_hour, self.birth_minute, city, nation
                )
        except Exception as e:
            raise Exception(f"Kerykeion初始化失败: {str(e)}")
    
    def get_planet_positions(self):
        """获取所有行星位置"""
        planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 
                   'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
        
        positions = {}
        for planet in planets:
            try:
                planet_data = getattr(self.subject, planet)
                positions[planet] = {
                    'sign': planet_data['sign'],
                    'sign_num': planet_data['sign_num'],
                    'position': float(planet_data['pos']),  # 在星座内的度数
                    'absolute_position': float(planet_data['abs_pos']),  # 绝对度数
                    'house': planet_data['house'],
                    'retrograde': planet_data['retrograde']
                }
            except Exception as e:
                positions[planet] = {'error': str(e)}
        
        # 添加南北交点
        try:
            positions['mean_node'] = {
                'sign': self.subject.mean_node['sign'],
                'position': float(self.subject.mean_node['pos'])
            }
        except:
            pass
        
        return positions
    
    def get_houses(self):
        """获取宫位"""
        houses = []
        for i in range(1, 13):
            try:
                house_attr = f"house_{i}"
                house_data = getattr(self.subject, house_attr)
                houses.append({
                    'house': i,
                    'sign': house_data['sign'],
                    'sign_num': house_data['sign_num'],
                    'position': float(house_data['pos'])
                })
            except:
                houses.append({'house': i, 'error': f'无法获取第{i}宫'})
        return houses
    
    def get_basic_info(self):
        """获取基本信息（上升、太阳、月亮）"""
        try:
            return {
                'ascendant': {
                    'sign': self.subject.first_house['sign'],
                    'position': float(self.subject.first_house['position'])
                },
                'sun': {
                    'sign': self.subject.sun['sign'],
                    'position': float(self.subject.sun['position'])
                },
                'moon': {
                    'sign': self.subject.moon['sign'],
                    'position': float(self.subject.moon['position'])
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_full_chart(self):
        """获取完整星盘数据"""
        return {
            'basic_info': self.get_basic_info(),
            'planets': self.get_planet_positions(),
            'houses': self.get_houses(),
            'birth_info': {
                'name': self.name,
                'datetime': f"{self.birth_year}-{self.birth_month:02d}-{self.birth_day:02d} {self.birth_hour:02d}:{self.birth_minute:02d}",
                'location': f"{self.city}, {self.nation}"
            }
        }


@app.route('/', methods=['GET'])
def home():
    """健康检查"""
    return jsonify({
        'status': 'online',
        'service': 'Astrology Chart Calculator',
        'version': '1.0.0',
        'message': '使用POST /calculate 计算星盘'
    })

@app.route('/calculate', methods=['POST', 'GET'])
def calculate():
    """计算星盘API"""
    if request.method == 'GET':
        # 从GET参数获取
        args = request.args
        data = {
            'name': args.get('name', 'User'),
            'birth_year': args.get('birth_year'),
            'birth_month': args.get('birth_month'),
            'birth_day': args.get('birth_day'),
            'birth_hour': args.get('birth_hour'),
            'birth_minute': args.get('birth_minute'),
            'city': args.get('city', ''),
            'nation': args.get('nation', ''),
            'lng': args.get('lng'),
            'lat': args.get('lat'),
            'tz_str': args.get('tz_str')
        }
    else:
        # 从POST JSON获取
        data = request.get_json()
    
    # 验证必要参数
    required = ['birth_year', 'birth_month', 'birth_day', 'birth_hour', 'birth_minute']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({
            'success': False,
            'error': f'缺少必要参数: {", ".join(missing)}'
        }), 400
    
    try:
        # 创建计算器实例
        calculator = BirthChartCalculator(
            name=data.get('name', 'User'),
            birth_year=data['birth_year'],
            birth_month=data['birth_month'],
            birth_day=data['birth_day'],
            birth_hour=data['birth_hour'],
            birth_minute=data['birth_minute'],
            city=data.get('city', 'Unknown'),
            nation=data.get('nation', 'Unknown'),
            lng=data.get('lng'),
            lat=data.get('lat'),
            tz_str=data.get('tz_str')
        )
        
        # 计算完整星盘
        chart_data = calculator.get_full_chart()
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """测试接口 - 返回示例数据"""
    return jsonify({
        'success': True,
        'data': {
            'basic_info': {
                'ascendant': {'sign': '天蝎座', 'position': 15.5},
                'sun': {'sign': '处女座', 'position': 23.4},
                'moon': {'sign': '金牛座', 'position': 7.8}
            },
            'planets': {
                'mercury': {'sign': '天秤座', 'position': 5.2, 'house': 3},
                'venus': {'sign': '狮子座', 'position': 12.3, 'house': 1}
            },
            'message': '这是测试数据，实际使用时请调用正式接口'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)