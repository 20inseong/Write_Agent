import datetime

# 천간(10)과 지지(12) 리스트 정의
STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

# 글자별 오행(목, 화, 토, 금, 수) 속성 매핑
ELEMENTS = {
    "갑": "목", "을": "목", "인": "목", "묘": "목",
    "병": "화", "정": "화", "사": "화", "오": "화",
    "무": "토", "기": "토", "진": "토", "술": "토", "축": "토", "미": "토",
    "경": "금", "신": "금", "유": "금",
    "임": "수", "계": "수", "해": "수", "자": "수"
}

# 양력 기준 매월 대략적인 절기 교입일 (1월 소한 ~ 12월 대설)
# 판타지 세계관 등에서 이 범위를 벗어나는 날짜가 들어와도 에러 없이 동작함
APPROX_SOLAR_TERMS = {
    1: 6, 2: 4, 3: 6, 4: 5, 5: 6, 6: 6,
    7: 7, 8: 8, 9: 8, 10: 8, 11: 7, 12: 7
}

def get_saju(year, month, day, hour):
    """
    생년월일시를 입력받아 간이 절기를 반영한 60갑자 사주를 반환
    """
    # 💡 [간이 절기 보정] 입력된 '일(day)'이 해당 월의 절기 교입일보다 작으면 이전 달로 취급
    saju_year = year
    saju_month = month
    term_day = APPROX_SOLAR_TERMS.get(month, 5) # 딕셔너리에 없는 가상의 월(13월 등)이면 평균 5일로 퉁침
    
    if day < term_day:
        saju_month -= 1
        if saju_month == 0:
            saju_month = 12
            saju_year -= 1 # 1월 소한 이전이면 전년도 취급
            
    # 양력 2월(입춘)이 사주상 새해(인월)의 시작이므로 이를 보정
    # 입춘 전(saju_month가 1인 경우)은 아직 전년도의 기운임
    if saju_month == 1:
        saju_year -= 1

    # 1. 연주: 보정된 saju_year를 기준으로 계산
    year_stem_idx = (saju_year - 4) % 10
    year_branch_idx = (saju_year - 4) % 12
    year_pillar = STEMS[year_stem_idx] + BRANCHES[year_branch_idx]

    # 2. 월주: 보정된 saju_month를 인월(2월)부터 순차적으로 매핑
    # 사주상 인월(양력 2월)이 지지 인덱스 2번("인")이 되도록 보정
    month_branch_idx = saju_month % 12
    month_stem_start = ((year_stem_idx % 5) * 2 + 2) % 10 
    
    # 2월이 사주의 첫 달이므로, 계산식에서 월 편차를 맞춰줌
    month_offset = (saju_month - 2) % 12 
    month_stem_idx = (month_stem_start + month_offset) % 10
    month_pillar = STEMS[month_stem_idx] + BRANCHES[month_branch_idx]

    # 3. 일주: 기존과 동일하게 무조건 날짜 카운트로 계산 (이세계 날짜 방어용 try-except 유지)
    try:
        date_obj = datetime.date(year, month, day)
        days_since_1ad = date_obj.toordinal()
    except ValueError:
        days_since_1ad = year * 365 + month * 30 + day

    day_idx = (days_since_1ad + 14) % 60
    day_stem_idx = day_idx % 10
    day_branch_idx = day_idx % 12
    day_pillar = STEMS[day_stem_idx] + BRANCHES[day_branch_idx]

    # 4. 시주: 기존 공식을 그대로 적용
    hour_branch_idx = ((hour + 1) // 2) % 12
    hour_stem_start = ((day_stem_idx % 5) * 2) % 10
    hour_stem_idx = (hour_stem_start + hour_branch_idx) % 10
    time_pillar = STEMS[hour_stem_idx] + BRANCHES[hour_branch_idx]

    return {
        "year": year_pillar,
        "month": month_pillar,
        "day": day_pillar,
        "time": time_pillar
    }

def analyze_five_elements(saju_dict):
    """
    도출된 사주 8글자의 오행 개수를 분석하여 딕셔너리로 반환하는 함수
    """
    counts = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    
    # 사주 딕셔너리의 값을 순회하며 오행 카운트 1씩 증가
    for pillar in saju_dict.values():
        stem, branch = pillar[0], pillar[1]
        counts[ELEMENTS[stem]] += 1
        counts[ELEMENTS[branch]] += 1
        
    return counts

def generate_saju_prompt(year, month, day, hour):
    """
    AI 프롬프트에 주입할 수 있도록 사주와 오행 결과를 자연스러운 텍스트로 가공하는 함수
    """
    saju = get_saju(year, month, day, hour)
    elements = analyze_five_elements(saju)
    
    # 지배적인 기운(가장 개수가 많은 오행) 추출
    dominant_element = max(elements, key=elements.get)
    
    prompt_text = (
        f"이 캐릭터의 생년월일시를 바탕으로 한 명리학적 기운은 {saju['year']}년, {saju['month']}월, {saju['day']}일, {saju['time']}시입니다. "
        f"오행의 구성은 목({elements['목']}), 화({elements['화']}), 토({elements['토']}), 금({elements['금']}), 수({elements['수']})이며, "
        f"가장 강한 기운은 '{dominant_element}'입니다. 이를 바탕으로 캐릭터를 묘사하고, 상황과 어울리는 성격의 의외성이나 숨겨진 기질을 입체적으로 글에 구현해주세요."
    )
    return prompt_text