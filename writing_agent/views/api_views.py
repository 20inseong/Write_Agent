import os
import json
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from google import genai
from google.genai import types

from ..models import Novel, StoryElement
from ..prompt import oov_extract_prompt

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