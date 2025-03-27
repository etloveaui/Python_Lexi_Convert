# utils/json_encoder.py
import json

class CustomJSONEncoder(json.JSONEncoder):
    """Section 객체 직렬화를 위한 사용자 정의 JSON 인코더"""
    def default(self, obj):
        # Section 객체나 기타 직렬화할 수 없는 객체 처리
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        
        # 기타 직렬화 불가능한 객체에 대한 처리
        try:
            return str(obj)
        except:
            return None
        
        return json.JSONEncoder.default(self, obj)
