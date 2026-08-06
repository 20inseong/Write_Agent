import os
import google.generativeai as genai
from dotenv import load_dotenv
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from .prompts import prompt_labels, system_prompt

load_dotenv()

def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")

# 블록의 틀을 세팅
def writer_setup(request: HttpRequest) -> HttpResponse:
   
    return render(
        request, 
        "writer_setup.html", 
        {"initial_block_index": 1})


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


def editor(request: HttpRequest) -> HttpResponse:
    ai_draft_text = ""
    
    if request.method == "POST":
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

        # 제미나이 API 세팅 (환경 변수에서 키 가져오기)
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("🚨 에러: .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다!")
            
        genai.configure(api_key=api_key)


        
        final_draft = ""
        previous_scene_summary = ""

        model = genai.GenerativeModel(
            model_name='gemini-flash-latest',
            system_instruction=system_prompt
        )

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
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(temperature=0.7)
                )
                
                scene_text = response.text.strip()
                final_draft += f"\n\n=== [장면 {i}] ===\n\n{scene_text}"
                
                previous_scene_summary = scene_text[-150:] if len(scene_text) > 150 else scene_text
                
            except Exception as e:
                print(f"API 호출 중 에러 발생: {e}")
                final_draft += f"\n\n[장면 {i} 생성 중 제미나이 API 오류가 발생했습니다.]\n에러 내용: {e}\n"

        ai_draft_text = final_draft.strip()

    return render(
        request, 
        "editor.html", 
        {"ai_content": ai_draft_text} 
    )
