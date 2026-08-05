from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")

# 블록의 틀을 세팅하고, AI 초안 생성 시작버튼을 클릭 시, 작성한 블록 인덱스와 내용을 터미널에 출력하는 함수
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

        # 2. 프롬프트 조립 (건너뜀)
        base_prompt = ""
        
        final_draft = ""
        previous_scene_summary = ""

        for block in sorted_blocks:
            # RAG DB에서 소설 설정집 가져오기
            # settings = get_rag_context()
            # 블록만의 독자적인 프롬프트를 만들건지 고민(구체적인 형태를 고민해야 함. => 할 거라면 장면 요약 프롬프트까지)

            # 3. AI에게 한 장면만 쓰게 하기
            # scene_text = call_ai_api(prompt)
            # final_draft += scene_text + "\n\n"
            
            # 4. 방금 쓴 장면을 요약해서 다음 바퀴(블록)로 넘겨주기
            # previous_scene_summary = summarize_for_next_scene(scene_text)
            pass
        
        # [임시 텍스트] AI가 응답을 주었다고 가정합니다.
        ai_draft_text = f"====== 조립된 프롬프트 내용 ======\n{prompt}"

    return render(
        request, 
        "editor.html", 
        {"ai_content": ai_draft_text} 
    )
