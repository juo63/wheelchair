from flask import Flask, render_template, request, jsonify, send_from_directory
from parser_filter import parse_user_input, filter_wheelchairs
from pathlib import Path
import pandas as pd
import urllib.parse
import os

app = Flask(__name__)

# 정적 파일 서빙을 위한 추가 라우트
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    """이미지 파일 서빙"""
    image_path = Path("static/images") / filename
    
    # 파일 크기 확인 (10MB 이상이면 제외)
    if image_path.exists():
        file_size = image_path.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            return "이미지 파일이 너무 큽니다", 413  # Request Entity Too Large
    
    return send_from_directory('static/images', filename, max_age=3600)  # 1시간 캐시

def get_image_path(product_name):
    """제품 이미지 경로 반환"""
    image_dir = Path("static/images")
    
    # 기본 파일명으로 시도
    image_path = image_dir / f"{product_name}.png"
    
    if image_path.exists():
        # 파일 크기 확인 (10MB 이상이면 제외)
        file_size = image_path.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            print(f"파일이 너무 큼 ({file_size} bytes): {product_name}.png")
            return None
            
        print(f"이미지 찾음: {product_name}.png (크기: {file_size} bytes)")
        # URL에서 안전하게 사용할 수 있도록 인코딩
        encoded_name = urllib.parse.quote(f"{product_name}.png")
        return f"/static/images/{encoded_name}"
    
    # MSL-T(24) -> MSL-T-24 변환 시도
    if "(" in product_name and ")" in product_name:
        converted_name = product_name.replace("(", "-").replace(")", "")
        image_path = image_dir / f"{converted_name}.png"
        if image_path.exists():
            # 파일 크기 확인
            file_size = image_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                print(f"변환된 파일이 너무 큼 ({file_size} bytes): {converted_name}.png")
                return None
                
            print(f"변환된 이미지 찾음: {converted_name}.png (크기: {file_size} bytes)")
            encoded_name = urllib.parse.quote(f"{converted_name}.png")
            return f"/static/images/{encoded_name}"
    
    print(f"이미지를 찾을 수 없음: {product_name}")
    # 파일이 없으면 None 반환
    return None

def format_recommendations(results_df):
    """추천 결과 포맷팅"""
    recommendations = []
    for _, row in results_df.iterrows():
        # 키워드 리스트 생성 (None이 아닌 경우만)
        keywords = [
            row['추천 키워드1'],
            row['추천 키워드2'],
            row['추천 키워드3']
        ]
        # None이나 NaN이 아닌 키워드만 필터링
        valid_keywords = [k for k in keywords if pd.notna(k) and k is not None]

        recommendations.append({
            'name': row['제품명'],
            'manufacturer': row['제조사'],
            'weight': row['무게(kg)'],
            'seatWidth': row['좌폭(cm)'],
            'keywords': valid_keywords,  # 유효한 키워드만 전달
            'image': get_image_path(row['제품명'])
        })
    return recommendations

@app.route('/')
def home():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/recommend', methods=['POST'])
def recommend():
    """휠체어 추천 API"""
    try:
        user_input = request.json.get('query', '')
        
        # 사용자 입력 처리
        conditions = parse_user_input(user_input)
        
        # 추천 결과 얻기
        results_df = filter_wheelchairs(conditions)
        
        if results_df.empty:
            return jsonify({
                'success': False,
                'message': '조건에 맞는 휠체어를 찾을 수 없습니다.'
            })
        
        # 결과 포맷팅
        recommendations = format_recommendations(results_df)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        })

@app.route('/api/quick-recommend', methods=['POST'])
def quick_recommend():
    """빠른 추천 API"""
    try:
        recommend_type = request.json.get('type', '')
        df = pd.read_excel("휠체어정보.xlsx")
        
        if recommend_type == "남성":
            # 기본형 휠체어 중 3개 랜덤 선택
            기본형_조건 = (
                df["추천 키워드1"].str.contains("기본형", na=False) |
                df["추천 키워드2"].str.contains("기본형", na=False) |
                df["추천 키워드3"].str.contains("기본형", na=False)
            )
            results_df = df[기본형_조건].sample(n=3)
        
        elif recommend_type == "여성":
            # 경량형 휠체어 중 3개 랜덤 선택
            경량형_조건 = (
                df["추천 키워드1"].str.contains("경량형", na=False) |
                df["추천 키워드2"].str.contains("경량형", na=False) |
                df["추천 키워드3"].str.contains("경량형", na=False)
            )
            results_df = df[경량형_조건].sample(n=3)
        
        elif recommend_type == "기본형":
            # 기본형 휠체어 중 3개 랜덤 선택
            기본형_조건 = (
                df["추천 키워드1"].str.contains("기본형", na=False) |
                df["추천 키워드2"].str.contains("기본형", na=False) |
                df["추천 키워드3"].str.contains("기본형", na=False)
            )
            results_df = df[기본형_조건].sample(n=3)
        
        elif recommend_type == "경량형":
            # 경량형 휠체어 중 3개 랜덤 선택
            경량형_조건 = (
                df["추천 키워드1"].str.contains("경량형", na=False) |
                df["추천 키워드2"].str.contains("경량형", na=False) |
                df["추천 키워드3"].str.contains("경량형", na=False)
            )
            results_df = df[경량형_조건].sample(n=3)
        
        elif recommend_type == "대형":
            # 대형 휠체어 (16.5kg 이상) 중 3개 랜덤 선택
            대형_조건 = df["무게(kg)"] >= 16.5
            results_df = df[대형_조건].sample(n=3)
        
        else:
            return jsonify({
                'success': False,
                'message': '잘못된 추천 유형입니다.'
            })
        
        if results_df.empty:
            return jsonify({
                'success': False,
                'message': '조건에 맞는 휠체어를 찾을 수 없습니다.'
            })
        
        # 결과 포맷팅
        recommendations = format_recommendations(results_df)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 