import os
import json
import re
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from google import genai
from google.genai import types
from django.utils import timezone

from ..models import Novel, StoryElement, CharacterDetail, FactionDetail, ItemDetail, LocationDetail, EventDetail, TemporaryDraft, Episode, AuthorProfile
from ..prompt import oov_extract_prompt, prompt_labels, system_prompt
from ..utils import generate_saju_prompt

@login_required
@require_POST
def verify_keywords_api(request: HttpRequest, novel_id: int = None) -> JsonResponse:
    novel = get_object_or_404(Novel, id=novel_id, author=request.user) if novel_id else None

    try:
        data = json.loads(request.body)
        blocks = data.get("blocks", [])

        # 모든 블록 입력 텍스트 병합
        all_user_input_text = ""
        for block in blocks:
            for val in block.values():
                if val:
                    all_user_input_text += f" {val}"

        # 1차 검증 (Python Fast-Match): DB 등록 키워드 스캔
        user_elements = StoryElement.objects.filter(novel=novel, author=request.user, is_deleted=False)
        matched_keywords = set()

        for element in user_elements:
            if not element.keyword_name:
                continue
            keyword_list = [k.strip() for k in element.keyword_name.split(',')]
            for kw in keyword_list:
                if kw and kw in all_user_input_text:
                    matched_keywords.add(kw)

        matched_keywords_list = list(matched_keywords)

        # 2차 검증 (LLM Context Extraction): 제미나이 호출
        api_key = os.environ.get("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)

        llm_input = (
            f"[기존 등록 키워드]: {', '.join(matched_keywords_list) if matched_keywords_list else '없음'}\n"
            f"[소설 텍스트]: {all_user_input_text}"
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=llm_input,
            config=types.GenerateContentConfig(
                system_instruction=oov_extract_prompt,
                temperature=0.1,  # 일관된 키워드 추출을 위한 낮은 온도
            )
        )

        extracted_text = response.text.strip()
        new_oov_keywords = []

        # '없음'이 아니면 쉼표 기준으로 파싱
        if extracted_text and extracted_text != "없음":
            new_oov_keywords = [k.strip() for k in extracted_text.split(',') if k.strip()]

        return JsonResponse({
            "status": "success",
            "matched": matched_keywords_list,
            "unregistered": new_oov_keywords
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
@require_POST
def generate_single_block_api(request: HttpRequest, novel_id: int = None) -> JsonResponse:
    novel = get_object_or_404(Novel, id=novel_id, author=request.user) if novel_id else None

    try:
        data = json.loads(request.body)
        block_data = data.get("block", {})
        previous_context = data.get("previous_context", "")

        unregistered_action = data.get("unregistered_action")
        unregistered_keywords = data.get("unregistered_keywords", [])
        
        if unregistered_action == 'stub' and novel and unregistered_keywords:
            for item in unregistered_keywords:
                word = item.get("word")
                category = item.get("category")
                
                if not word or not category:
                    continue # 둘 중 하나라도 누락되면 패스

                # 기본 뼈대 요소 생성
                new_element = StoryElement.objects.create(
                    author=request.user, novel=novel, category=category,
                    name=word, keyword_name=word, folder_path="/"
                )
                
                # 카테고리별 분기 처리하여 1:1 세부 테이블 생성
                if category == 'CHARACTER':
                    CharacterDetail.objects.create(element=new_element)
                elif category == 'FACTION':
                    FactionDetail.objects.create(element=new_element)
                elif category == 'ITEM':
                    ItemDetail.objects.create(element=new_element)
                elif category == 'LOCATION':
                    LocationDetail.objects.create(element=new_element)
                elif category == 'EVENT':
                    EventDetail.objects.create(element=new_element)

        # 텍스트 병합 및 RAG 스캔
        all_user_input_text = " ".join([str(v) for v in block_data.values() if v])
        user_elements = StoryElement.objects.filter(novel=novel, author=request.user, is_deleted=False) if novel else StoryElement.objects.none()
        
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
                        detail_text = f"이명: {d.aliases}, 주력능력: {d.main_skill}, 무기: {d.weapon}, 성격: {d.personality}, 욕망: {d.desire}, 금기: {d.taboo}"
                        if d.birthday:
                            numbers = re.findall(r'\d+', d.birthday)
                            if len(numbers) >= 4:
                                saju_context = generate_saju_prompt(*map(int, numbers[:4]))
                                detail_text += f" | {saju_context}"
                    elif element.category == 'FACTION' and hasattr(element, 'faction_detail'):
                        d = element.faction_detail
                        detail_text = f"성향: {d.alignment}, 이념: {d.ideology}, 핵심인물: {d.key_members}, 자산/규모: {d.assets}"
                    elif element.category == 'ITEM' and hasattr(element, 'item_detail'):
                        d = element.item_detail
                        detail_text = f"외형: {d.appearance}, 효과: {d.effect}, 제약: {d.penalty}, 기원: {d.origin}"
                    elif element.category == 'LOCATION' and hasattr(element, 'location_detail'):
                        d = element.location_detail
                        detail_text = f"기후: {d.climate}, 통치자: {d.ruler}, 랜드마크: {d.significance}, 숨겨진역사: {d.hidden_history}"
                    elif element.category == 'EVENT' and hasattr(element, 'event_detail'):
                        d = element.event_detail
                        detail_text = f"주체: {d.participants}, 발발원인: {d.trigger}, 파급력: {d.impact}"
                    
                    matched_contexts.append(f"[{category_name}: {element.name}] {detail_text}")
                    break
        
        enhanced_system_prompt = system_prompt
        if matched_contexts:
            enhanced_system_prompt += "\n\n[현재 장면 관련 참고 설정]\n" + "\n".join(matched_contexts)

        # 제미나이 프롬프트 조립
        instructions_list = []
        for k, v in block_data.items():
            if v and str(v).strip():
                label = prompt_labels.get(k, k) 
                instructions_list.append(f"- {label}: {str(v).strip()}")
        
        user_prompt = f"다음 지시사항에 따라 새로운 장면을 작성해 주세요:\n" + "\n".join(instructions_list)
        if previous_context:
            user_prompt = f"[이전 장면의 끝부분 문맥]:\n{previous_context}\n\n위 문맥에 자연스럽게 이어지도록 " + user_prompt

        # 제미나이 호출 및 JSON 반환
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=enhanced_system_prompt,
                temperature=0.7,
            )
        )
        # AI 원본 응답에서 불필요한 머리말('장면 1' 등)을 제거
        ai_raw_output = response.text.strip()
        pure_scene_text = clean_generated_text(ai_raw_output)
        
        # 정제된 텍스트(pure_scene_text)를 프론트엔드로 반환
        return JsonResponse({"status": "success", "scene_text": pure_scene_text})

    except Exception as e:
        error_msg = str(e).upper()
        if "503" in error_msg or "UNAVAILABLE" in error_msg:
            return JsonResponse({"status": "error", "message": "현재 AI 서버 접속자가 많습니다. 1~2분 뒤 다시 시도해주세요."})
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
@require_POST
def save_temp_draft(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body)
        
        # 프론트에서 넘어온 JSON 데이터 파싱 (안전하게 get으로 추출)
        ai_content = data.get('ai_content', '')
        user_content = data.get('user_content', '')
        setup_context = data.get('setup_context', None)

        # 무조건 업데이트할 필드만 먼저 세팅
        defaults_data = {
            'ai_draft_content': ai_content,
            'user_content': user_content,
        }

        # 에디터에서 setup_context 데이터를 명시적으로 보냈을 때만 업데이트 (안 보냈으면 원본 보존)
        if setup_context: 
            defaults_data['setup_context'] = setup_context

        # 현재 로그인한 작가 기준으로 임시저장 데이터를 덮어쓰거나 신규 생성
        draft, created = TemporaryDraft.objects.update_or_create(
            author=request.user,
            is_deleted=False,
            defaults=defaults_data
        )

        local_time = timezone.localtime(draft.updated_at)

        return JsonResponse({
            'status': 'success',
            'message': '임시 저장 완료',
            'updated_at': local_time.strftime('%H:%M:%S')
        })

    except Exception as e:
        # 에러 발생
        print(f"🚨 임시 저장 백엔드 에러 원인: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def clean_generated_text(text: str) -> str:
    """AI가 서두에 출력한 장면 번호, 소제목, 불필요한 마크다운 헤더를 정제하는 함수"""
    if not text:
        return ""
    
    # 서두에 등장하는 [장면 1], 장면 1:, # 장면 1, 1장 등 패턴 제거
    pattern = r'^(?:#+\s*)?(?:\[\s*)?(?:장면|Scene|제\s*\d+\s*장|\d+\s*장)(?:\s*\d+)?(?:\s*[:\-\]\.\)]*)?\s*\n*'
    cleaned_text = re.sub(pattern, '', text.strip(), flags=re.IGNORECASE)
    
    return cleaned_text.strip()

@login_required
@require_POST
def save_episode_api(request: HttpRequest, novel_id: int = None) -> JsonResponse:
    # 💡 모든 로직을 try 안으로 넣어서, 에러가 나더라도 브라우저가 원인을 알 수 있게 함!
    try:
        if novel_id:
            novel = get_object_or_404(Novel, id=novel_id, author=request.user)
        else:
            # 존재하지 않는 필드(description 등) 때문에 에러가 나지 않도록 가장 기본 필드만 사용
            novel, created = Novel.objects.get_or_create(
                author=request.user,
                title="자유 창작 노트 (기본)"
            )
        
        data = json.loads(request.body)
        title = data.get('title', '새 에피소드')
        content = data.get('content', '')
        
        # 일치도(%)가 문자열로 넘어올 수 있으니 정수형으로 안전하게 변환
        try:
            ai_similarity = int(data.get('ai_similarity', 0))
        except ValueError:
            ai_similarity = 0

        # 메인 테이블에 완성본 최종 저장
        Episode.objects.create(
            author=request.user,
            novel=novel,
            title=title,
            content=content,
            ai_similarity=ai_similarity
        )

        # 완성본 저장이 끝났으므로 기존 임시저장(TemporaryDraft) 내용 비우기
        draft = TemporaryDraft.objects.filter(author=request.user, is_deleted=False).first()
        if draft:
            draft.ai_draft_content = ""
            draft.user_content = ""
            draft.setup_context = "{}"
            draft.save()

        return JsonResponse({'status': 'success', 'message': '성공적으로 저장되었습니다.'})

    except Exception as e:
        # 에러가 나도 서버가 죽지 않고 구체적인 이유를 프론트로 전달해 줌
        print(f"🚨 완성본 저장 API 에러: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def update_settings_api(request):
    try:
        data = json.loads(request.body)
        profile, _ = AuthorProfile.objects.get_or_create(user=request.user)
        
        # 프론트에서 보낸 데이터 확인 및 업데이트
        if 'ai_temperature' in data:
            profile.ai_temperature = float(data['ai_temperature'])
        if 'is_dark_mode' in data:
            profile.is_dark_mode = bool(data['is_dark_mode'])
            
        profile.save()
        return JsonResponse({"status": "success", "message": "설정이 저장되었습니다."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@login_required
@require_POST
def delete_account_api(request):
    try:
        user = request.user
        user.is_active = False # 계정을 잠가서 로그인 불가능하게 만듦
        user.save()
        return JsonResponse({"status": "success", "message": "계정이 비활성화되었습니다."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)