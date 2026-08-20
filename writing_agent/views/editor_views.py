import os
import json
from dotenv import load_dotenv
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from google import genai
from google.genai import types
import re

from ..models import Novel, StoryElement, CharacterDetail, FactionDetail, ItemDetail, LocationDetail, EventDetail
from ..prompt import prompt_labels, system_prompt
from ..utils import generate_saju_prompt

load_dotenv()

@login_required
def writer_setup(request: HttpRequest, novel_id: int = None) -> HttpResponse:
    novel = get_object_or_404(Novel, id=novel_id, author=request.user) if novel_id else None
    return render(
        request, 
        "writer_setup.html", 
        {"initial_block_index": 1, "novel": novel}
    )

@login_required
@require_GET
def add_block(request: HttpRequest) -> HttpResponse:
    try:
        block_index = int(request.GET.get("index", "2"))
    except ValueError:
        block_index = 2
    return render(
        request,
        "block_partial.html",
        {"block_index": block_index},
    )

@login_required
def editor(request: HttpRequest, novel_id: int = None) -> HttpResponse:
    novel = get_object_or_404(Novel, id=novel_id, author=request.user) if novel_id else None
    ai_draft_text = ""
    
    if request.method == "POST":
        action = request.POST.get("unregistered_action", "")

        # 작가가 팝업에서 수동으로 작성한 데이터 저장
        if action == 'manual':
            manual_data_str = request.POST.get("manual_setup_data", "{}")
            try:
                manual_data = json.loads(manual_data_str)
                for word, data in manual_data.items():
                    category = data.get("category", "CHARACTER")
                    details = data.get("details", {})

                    # 뼈대 생성 (폴더는 기본 '/' 위치로 자동 지정)
                    new_element = StoryElement.objects.create(
                        author=request.user,
                        novel=novel,
                        category=category,
                        name=word,
                        keyword_name=word,
                        folder_path="/"
                    )

                    # 카테고리별 세부 설정 저장
                    if category == 'CHARACTER':
                        CharacterDetail.objects.create(
                            element=new_element,
                            aliases=details.get("aliases", ""),
                            birthday=details.get("birthday", ""),
                            main_skill=details.get("main_skill", ""),
                            level=details.get("level", ""),
                            weapon=details.get("weapon", ""),
                            clothing=details.get("clothing", ""),
                            personality=details.get("personality", ""),
                            appearance=details.get("appearance", ""),
                            desire=details.get("desire", ""),
                            taboo=details.get("taboo", ""),
                            allies=details.get("allies", ""),
                            enemies=details.get("enemies", ""),
                            other_details=details.get("other_details", "")
                        )
                    elif category == 'FACTION':
                        FactionDetail.objects.create(
                            element=new_element,
                            alignment=details.get("alignment", ""),
                            base_location=details.get("base_location", ""),
                            ideology=details.get("ideology", ""),
                            hierarchy=details.get("hierarchy", ""),
                            key_members=details.get("key_members", ""),
                            assets=details.get("assets", ""),
                            other_details=details.get("other_details", "")
                        )
                    elif category == 'ITEM':
                        ItemDetail.objects.create(
                            element=new_element,
                            item_type=details.get("item_type", ""),
                            appearance=details.get("appearance", ""),
                            effect=details.get("effect", ""),
                            penalty=details.get("penalty", ""),
                            origin=details.get("origin", ""),
                            other_details=details.get("other_details", "")
                        )
                    elif category == 'LOCATION':
                        LocationDetail.objects.create(
                            element=new_element,
                            region=details.get("region", ""),
                            ruler=details.get("ruler", ""),
                            climate=details.get("climate", ""),
                            significance=details.get("significance", ""),
                            hidden_history=details.get("hidden_history", ""),
                            other_details=details.get("other_details", "")
                        )
                    elif category == 'EVENT':
                        EventDetail.objects.create(
                            element=new_element,
                            timeline=details.get("timeline", ""),
                            participants=details.get("participants", ""),
                            trigger=details.get("trigger", ""),
                            impact=details.get("impact", ""),
                            other_details=details.get("other_details", "")
                        )
            except Exception as e:
                print(f"수동 설정 DB 저장 중 에러: {e}")

        # 뼈대(이름)만 빈 껍데기로 임시 저장 (수동 작성 패스 시)
        elif action == 'stub':
            keywords_str = request.POST.get("unregistered_keywords", "")
            if keywords_str:
                keywords_list = [k.strip() for k in keywords_str.split(',') if k.strip()]
                for word in keywords_list:
                    new_element = StoryElement.objects.create(
                        author=request.user,
                        novel=novel,
                        category='CHARACTER', # 기본값은 인물로
                        name=word,
                        keyword_name=word,
                        folder_path="/"
                    )
                    CharacterDetail.objects.create(element=new_element)

        # 빈 딕셔너리 생성
        block_data={}

        # 블록 데이터 추출
        for key, value in request.POST.items():
            if key == "csrfmiddlewaretoken":
                continue
            
            # 태그 쪼개기
            parts = key.rsplit('_', 1)
            if len(parts) == 2 and parts[1].isdigit():
                field_name = parts[0]  # 'goal_chars', 'start', 'climax' 등
                block_num = parts[1]   # '1', '2' 등

                # 처음 보는 블록 번호일 때, 방(딕셔너리)을 새로 만들기
                if block_num not in block_data:
                    block_data[block_num] = {}
                
                # 방 안에 데이터 삽입
                block_data[block_num][field_name] = value

        # 번호 순서대로 리스트 구현
        sorted_blocks = [block_data[num] for num in sorted(block_data.keys(), key=int)]

        print("====== 블록 데이터 정리 ======")
        for i, block in enumerate(sorted_blocks, 1):
            print(f"[블록 {i}] {block}")
        print("===========================================")

        # 작가가 입력한 모든 블록의 텍스트를 하나의 긴 끈으로 합치기
        all_user_input_text = ""
        for block in sorted_blocks:
            for v in block.values():
                all_user_input_text += f" {v}"

        # DB를 뒤져서 합친 텍스트 안에 키워드가 있는지 확인
        if novel:
            user_elements = StoryElement.objects.filter(novel=novel, author=request.user, is_deleted=False)
        else:
            user_elements = StoryElement.objects.none()

        matched_contexts = []
        
        for element in user_elements:
            if not element.keyword_name:
                continue

            keyword_list = [k.strip() for k in element.keyword_name.split(',')]
            for kw in keyword_list:
                if kw and kw in all_user_input_text:
                    category_name = element.get_category_display()
                    detail_text = ""
                    if element.category == 'CHARACTER' and hasattr(element, 'character_detail'):
                        d = element.character_detail
                        detail_text = f"이명/별호: {d.aliases}, 주력능력: {d.main_skill}, 무기: {d.weapon}, 성격: {d.personality}, 외형: {d.appearance}, 욕망: {d.desire}, 금기: {d.taboo}"
                        
                        if d.birthday:
                            # "1024년 5월 15일 14시" 같은 문자열에서 숫자 4개 추출
                            numbers = re.findall(r'\d+', d.birthday)
                            if len(numbers) >= 4:
                                year, month, day, hour = map(int, numbers[:4])
                                # utils.py의 사주/오행 프롬프트 텍스트를 받아와서 캐릭터 디테일에 덧붙임
                                saju_context = generate_saju_prompt(year, month, day, hour)
                                detail_text += f" | {saju_context}"
                    elif element.category == 'FACTION' and hasattr(element, 'faction_detail'):
                        d = element.faction_detail
                        detail_text = f"성향: {d.alignment}, 본거지: {d.base_location}, 이념: {d.ideology}, 핵심인물: {d.key_members}, 자산/규모: {d.assets}"
                    elif element.category == 'ITEM' and hasattr(element, 'item_detail'):
                        d = element.item_detail
                        detail_text = f"분류: {d.item_type}, 외형: {d.appearance}, 효과: {d.effect}, 제약: {d.penalty}, 기원: {d.origin}"
                    elif element.category == 'LOCATION' and hasattr(element, 'location_detail'):
                        d = element.location_detail
                        detail_text = f"지역: {d.region}, 통치자: {d.ruler}, 기후: {d.climate}, 랜드마크: {d.significance}, 숨겨진역사: {d.hidden_history}"
                    elif element.category == 'EVENT' and hasattr(element, 'event_detail'):
                        d = element.event_detail
                        detail_text = f"시점: {d.timeline}, 주체: {d.participants}, 발발원인: {d.trigger}, 파급력: {d.impact}"
                    
                    matched_contexts.append(f"[{category_name}: {element.name}] {detail_text}")
                    break
        
        # 찾은 설정들을 하나로 묶기
        rag_context_text = "\n".join(matched_contexts)
        
        print("===== AI에게 주입되는 DB 설정 =====")
        print(rag_context_text if rag_context_text else "추출된 키워드 없음")
        print("===================================")

        # 기존 system_prompt에 DB 설정을 덧붙여서 최종 시스템 프롬프트 완성
        enhanced_system_prompt = system_prompt
        if rag_context_text:
            enhanced_system_prompt += f"\n\n[현재 장면 관련 참고 설정]\n{rag_context_text}"


        # 제미나이 API 세팅 (환경 변수에서 키 가져오기)
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("🚨 에러: .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다!")
            
        client = genai.Client(api_key=api_key)
        
        final_draft = ""
        previous_scene_summary = ""

        for i, block in enumerate(sorted_blocks, 1):
            instructions_list = []
            
            # 번역기를 거쳐서 유저 프롬프트 조립
            for k, v in block.items():
                if v.strip():  # 내용이 비어있지 않은 경우만 처리
                    # 사전에 있는 키면 한글 설명을, 없으면 원래 키(k)를 사용
                    label = prompt_labels.get(k, k) 
                    instructions_list.append(f"- {label}: {v.strip()}")
            
            block_instructions = "\n".join(instructions_list)
            user_prompt = f"다음 지시사항에 따라 [장면 {i}]을(를) 작성해 주세요:\n{block_instructions}"
            
            # 이전 장면이 있다면 문맥 릴레이 (마지막 150자)
            if previous_scene_summary:
                user_prompt = f"[이전 장면의 끝부분 문맥]:\n{previous_scene_summary}\n\n위 문맥에 자연스럽게 이어지도록 " + user_prompt

            print(f"--- [블록 {i}] AI에게 전송하는 프롬프트 ---\n{user_prompt}\n---------------------------")

            # 제미나이 API 호출
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=enhanced_system_prompt,
                        temperature=0.7,
                    )
                )
                
                scene_text = response.text.strip()
                final_draft += f"\n\n=== [장면 {i}] ===\n\n{scene_text}"
                
                previous_scene_summary = scene_text[-150:] if len(scene_text) > 150 else scene_text
                
            except Exception as e:
                print(f"API 호출 중 에러 발생: {e}")
                error_msg = str(e).upper()
                
                # 503 과부하 에러인 경우 부드러운 안내 메시지 출력
                if "503" in error_msg or "UNAVAILABLE" in error_msg:
                    final_draft += f"\n\n [장면 {i}] 현재 AI 서버에 접속자가 많아 일시적인 지연이 발생하고 있습니다. 1~2분 뒤에 다시 [생성] 버튼을 눌러주세요.\n"
                else:
                    # 그 외 알 수 없는 에러
                    final_draft += f"\n\n [장면 {i}] 초안을 생성하는 도중 알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.\n"

        ai_draft_text = final_draft.strip()

    return render(
        request, 
        "editor.html", 
        {"ai_content": ai_draft_text} 
    )