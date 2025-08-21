import pandas as pd
import re

### 1. 사용자 입력 → 조건 변환 함수 ###
def parse_user_input(text):
    조건 = {}
    
    # 성별 키워드
    남성_키워드 = ["남성", "남자", "할아버지", "아저씨", "남편"]
    여성_키워드 = ["여성", "여자", "할머니", "아주머니", "부인"]
    
    if any(word in text for word in 남성_키워드):
        조건["성별"] = "남"
        if "체중" not in 조건:
            조건["체중"] = 70
    elif any(word in text for word in 여성_키워드):
        조건["성별"] = "여"
        if "체중" not in 조건:
            조건["체중"] = 55

    # 체중 추출
    weight_patterns = [
        r'(\d+)\s*(kg|킬로|키로|㎏)',
        r'몸무게\s*(\d+)',
        r'체중\s*(\d+)',
        r'(\d+)\s*k',
    ]
    for pattern in weight_patterns:
        weight_match = re.search(pattern, text)
        if weight_match:
            체중 = int(weight_match.group(1))
            조건["체중"] = 체중
            break

    # 연령 추출
    age_patterns = [
        r'(\d+)\s*(?:살|세|대)',
        r'(?:나이|연세|연령)[가이]?\s*(\d+)',
    ]
    for pattern in age_patterns:
        age_match = re.search(pattern, text)
        if age_match:
            연령 = int(age_match.group(1))
            조건["연령"] = 연령
            
            # 연령대만 있는 경우 다른 조건들은 무시
            if len(text.split()) <= 3 and not any(word in text for word in 남성_키워드 + 여성_키워드):  # 성별이나 체중 정보가 없을 때
                return {"연령": 연령}  # 연령만 반환
            
            # 연령대별 설정
            if 연령 >= 70:  # 70대 이상
                조건["좌폭_최대"] = 44  # 넓은 좌폭
                조건["고령자"] = True
                조건["무게_최대"] = 16  # 고령자는 16kg까지 허용
            else:  # 60대
                조건["좌폭_최대"] = 42  # 표준 좌폭
                조건["활동적"] = True
                조건["무게_최대"] = 15  # 60대는 15kg 제한
            break

    # 가벼운 휠체어 조건
    가벼움_키워드 = [
        "가벼운", "가볍", "경량", "가벼워", 
        "무겁지 않은", "가벼웠으면", "가벼웠음",
        "가볍게", "가벼운게", "가벼운것",
        "끌기 쉬운", "끌기쉬운", "끌기편한",
        "이동하기 쉬운", "이동이 쉬운"
    ]
    if any(word in text for word in 가벼움_키워드):
        조건["가벼움_요청"] = True
        조건["무게_최대"] = 14  # 14kg 이하로 제한

    # 대형 휠체어 조건
    대형_키워드 = [
        "큰", "대형", "크게", "큰거",
        "큰 휠체어", "큰것", "큰게"
    ]
    if any(word in text for word in 대형_키워드):
        조건["대형"] = True

    # 대형휠 조건
    대형휠_키워드 = [
        "큰 바퀴", "바퀴가 큰", "큰바퀴",
        "24인치", "24", "8인치"
    ]
    if any(word in text for word in 대형휠_키워드):
        조건["대형휠"] = True

    # 차량 관련 조건
    차량_키워드 = [
        "차에 실", "차량", "차에실", "차싣", 
        "트렁크", "자동차", "차boot", 
        "차 트렁크", "차에 넣", "차에넣",
        "차에 싣", "차에싣", "차로", "차타고",
        "운전", "드라이브"
    ]
    if any(word in text for word in 차량_키워드):
        조건["용도"] = "차량탑재"

    return 조건

### 2. 조건 → 휠체어 필터링 함수 ###
def parse_weight(val):
    """
    무게 문자열을 파싱하여 (최소값, 최대값) 튜플로 반환
    예:
    - "13.3~16" → (13.3, 16.0)
    - "16" → (16.0, 16.0)
    - "13.3" → (13.3, 13.3)
    """
    if isinstance(val, (int, float)):
        return (float(val), float(val))
    
    if not isinstance(val, str):
        return (99.0, 99.0)

    # 범위 형식 (예: "13.3~16")
    if "~" in val:
        try:
            min_val, max_val = val.split("~")
            return (float(min_val), float(max_val))
        except:
            return (99.0, 99.0)
    
    # 단일 숫자 형식
    try:
        numbers = re.findall(r'\d+(?:\.\d+)?', val)
        if numbers:
            num = float(numbers[0])
            return (num, num)
    except:
        pass
    
    return (99.0, 99.0)

def parse_min_seat_width(val):
    if isinstance(val, str):
        numbers = [int(x) for x in re.findall(r'\d+', val)]
        return min(numbers) if numbers else 99
    return 99

def filter_wheelchairs(조건, 엑셀파일="휠체어정보.xlsx"):
    df = pd.read_excel(엑셀파일)

    # 무게 전처리
    df["무게_범위"] = df["무게(kg)"].apply(parse_weight)
    df["무게_최소"] = df["무게_범위"].apply(lambda x: x[0])
    df["무게_최대"] = df["무게_범위"].apply(lambda x: x[1])
    
    # 좌폭 전처리
    df["좌폭_min"] = df["좌폭(cm)"].apply(parse_min_seat_width)

    filtered = df.copy()

    # 점수 기반 필터링 시스템
    filtered["점수"] = 0

    # 연령대만 있는 경우 기본형 제품만 필터링
    if len(조건.keys()) == 1 and "연령" in 조건:
        기본형_조건 = (
            filtered["추천 키워드1"].str.contains("기본형", na=False) |
            filtered["추천 키워드2"].str.contains("기본형", na=False) |
            filtered["추천 키워드3"].str.contains("기본형", na=False)
        )
        filtered = filtered[기본형_조건]
        if filtered.empty:
            return pd.DataFrame(columns=["제품명", "제조사", "무게(kg)", "좌폭(cm)", "추천 키워드1", "추천 키워드2", "추천 키워드3"])
        # 랜덤으로 정렬
        filtered = filtered.sample(frac=1)
        결과 = filtered[["제품명", "제조사", "무게(kg)", "좌폭(cm)", "추천 키워드1", "추천 키워드2", "추천 키워드3"]].head(3)
        return 결과

    # 대형휠 요청 시
    if 조건.get("대형휠"):
        대형휠_조건 = (
            filtered["추천 키워드1"].str.contains("대형휠", na=False) |
            filtered["추천 키워드2"].str.contains("대형휠", na=False) |
            filtered["추천 키워드3"].str.contains("대형휠", na=False)
        )
        # 대형휠 제품만 필터링
        filtered = filtered[대형휠_조건]
        if filtered.empty:
            return pd.DataFrame(columns=["제품명", "제조사", "무게(kg)", "좌폭(cm)", "추천 키워드1", "추천 키워드2", "추천 키워드3"])

    # 기본 조건 설정
    경량형_조건 = (
        filtered["추천 키워드1"].str.contains("경량형", na=False) |
        filtered["추천 키워드2"].str.contains("경량형", na=False) |
        filtered["추천 키워드3"].str.contains("경량형", na=False)
    )
    기본형_조건 = (
        filtered["추천 키워드1"].str.contains("기본형", na=False) |
        filtered["추천 키워드2"].str.contains("기본형", na=False) |
        filtered["추천 키워드3"].str.contains("기본형", na=False)
    )

    # 1순위: 구체적 요구사항 (가벼움, 끌기 쉬움 등)
    if 조건.get("가벼움_요청"):
        # 경량형 제품 우선
        filtered.loc[경량형_조건, "점수"] += 8
        # 무게가 더 가벼운 제품 추가 점수
        filtered.loc[filtered["무게_최대"] <= 13, "점수"] += 3
        filtered.loc[filtered["무게_최대"] <= 12, "점수"] += 2
        filtered.loc[filtered["무게_최대"] <= 11, "점수"] += 1
        조건["무게_최대"] = 14  # 14kg 이하로 제한
    
    # 2순위: 체중 기반 추천
    else:
        체중 = 조건.get("체중", 70)  # 기본값 70kg
        if 체중 <= 50:  # 50kg 이하
            # 경량형 우선
            filtered.loc[경량형_조건, "점수"] += 8
            filtered.loc[filtered["무게_최대"] <= 13, "점수"] += 3
            filtered.loc[filtered["무게_최대"] <= 12, "점수"] += 2
            filtered.loc[filtered["무게_최대"] <= 11, "점수"] += 1
            조건["무게_최대"] = 14  # 14kg 이하로 제한
        elif 체중 <= 80:  # 50~80kg
            # 기본형 우선
            filtered.loc[기본형_조건, "점수"] += 8
            # 3순위: 성별 기반 추천 (체중이 50~80kg인 경우에만 성별 고려)
            if 조건.get("성별") == "여":
                filtered.loc[경량형_조건, "점수"] += 4  # 여성은 경량형에 추가 점수
            조건["무게_최대"] = 16  # 16kg 이하로 제한
        else:  # 80kg 초과
            # 대형 제품 (16.5kg 이상) 우선
            대형_조건 = filtered["무게_최대"] >= 16.5
            filtered.loc[대형_조건, "점수"] += 8
            
            # 결과 정렬 및 선택
            filtered = filtered.sample(frac=1)  # 전체 데이터 랜덤 섞기
            filtered = filtered.sort_values("점수", ascending=False)
            
            # 대형 제품 2개 선택
            대형_결과 = filtered[대형_조건].head(2)
            
            # 기본형 제품 1개 랜덤 선택
            기본형_결과 = filtered[기본형_조건 & ~filtered.index.isin(대형_결과.index)].sample(n=1)
            
            # 결과 합치기
            결과 = pd.concat([대형_결과, 기본형_결과])
            return 결과[["제품명", "제조사", "무게(kg)", "좌폭(cm)", "추천 키워드1", "추천 키워드2", "추천 키워드3"]]

    # 차량탑재 조건 (13.3kg 이하만)
    if "용도" in 조건 and 조건["용도"] == "차량탑재":
        # 13.3kg 이하 필터링
        차량가능_조건 = filtered["무게_최대"] <= 13.3
        차량탑재_조건 = (
            filtered["추천 키워드1"].str.contains("차량탑재", na=False) |
            filtered["추천 키워드2"].str.contains("차량탑재", na=False) |
            filtered["추천 키워드3"].str.contains("차량탑재", na=False)
        )
        
        # 차량탑재 가능한 제품들
        차량적합 = 차량가능_조건 & 차량탑재_조건
        
        if 차량적합.any():
            # 기본 점수
            filtered.loc[차량적합, "점수"] += 3
            
            # 무게에 따른 추가 점수
            filtered.loc[차량적합 & (filtered["무게_최대"] <= 11), "점수"] += 4
            filtered.loc[차량적합 & (filtered["무게_최대"] > 11) & (filtered["무게_최대"] <= 12), "점수"] += 3
            filtered.loc[차량적합 & (filtered["무게_최대"] > 12) & (filtered["무게_최대"] <= 13), "점수"] += 2
            filtered.loc[차량적합 & (filtered["무게_최대"] > 13) & (filtered["무게_최대"] <= 13.3), "점수"] += 1

    # 무게 제한 조건
    if "무게_최대" in 조건:
        filtered = filtered[filtered["무게_최대"] <= 조건["무게_최대"]]

    # 좌폭 제한 조건
    if "좌폭_최대" in 조건:
        filtered = filtered[filtered["좌폭_min"] <= 조건["좌폭_최대"]]

    # 결과가 없으면 빈 DataFrame 반환
    if filtered.empty:
        return pd.DataFrame(columns=["제품명", "제조사", "무게(kg)", "좌폭(cm)", "추천 키워드1", "추천 키워드2", "추천 키워드3"])

    # 점수로 정렬하고 같은 점수는 랜덤 정렬
    filtered = filtered.sample(frac=1)  # 전체 데이터 랜덤 섞기
    filtered = filtered.sort_values("점수", ascending=False)

    # 필요한 컬럼만 선택하여 반환 (최대 3개)
    결과 = filtered[["제품명", "제조사", "무게(kg)", "좌폭(cm)", "추천 키워드1", "추천 키워드2", "추천 키워드3"]].head(3)
    return 결과

### 3. 실행 ###
if __name__ == "__main__":
    print("휠체어 추천을 위한 정보를 입력해주세요.")
    사용자문장 = input("예: 70대 여성이고 45kg이며 외출용으로 가끔 써요\n입력: ")
    조건 = parse_user_input(사용자문장)

    print("\n[조건 추출 결과]")
    for key, value in 조건.items():
        print(f"{key}: {value}")

    결과 = filter_wheelchairs(조건)
    print("\n[추천 결과]")
    if 결과.empty:
        print("조건에 맞는 휠체어가 없습니다.")
    else:
        print(결과)
