import os
from dotenv import load_dotenv
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET
from .prompt import prompt_labels, system_prompt
from .models import StoryElement
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from google import genai
from google.genai import types
from .models import Novel
from django.shortcuts import get_object_or_404, redirect
from .models import Novel, StoryElement, CharacterDetail, FactionDetail, ItemDetail, LocationDetail, EventDetail
from django.urls import reverse

load_dotenv()

def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "landing.html")


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard.html")


# 회원가입 뷰
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 회원가입 성공 시 자동 로그인
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})


# 블록의 틀을 세팅
@login_required
def writer_setup(request: HttpRequest) -> HttpResponse:
   
    return render(
        request, 
        "writer_setup.html", 
        {"initial_block_index": 1})


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
def world_list_view(request):
    my_novels = Novel.objects.filter(author=request.user)
    return render(request, "world_list.html", {"novels": my_novels})


@login_required
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

        # 작가가 입력한 모든 블록의 텍스트를 하나의 긴 끈으로 합치기
        all_user_input_text = ""
        for block in sorted_blocks:
            for v in block.values():
                all_user_input_text += f" {v}"

        # DB를 뒤져서 합친 텍스트 안에 키워드가 있는지 확인
        user_elements = StoryElement.objects.filter(author=request.user, is_deleted=False)
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
                final_draft += f"\n\n[장면 {i} 생성 중 제미나이 API 오류가 발생했습니다.]\n에러 내용: {e}\n"

        ai_draft_text = final_draft.strip()

    return render(
        request, 
        "editor.html", 
        {"ai_content": ai_draft_text} 
    )

@login_required
def world_category_view(request, novel_id):
    novel = get_object_or_404(Novel, id=novel_id, author=request.user)
    return render(request, "world_category.html", {"novel": novel})


@login_required
def world_element_list_view(request, novel_id, category):
    novel = get_object_or_404(Novel, id=novel_id, author=request.user)

    category_map = {
        '인물': 'CHARACTER',
        '단체': 'FACTION',
        '물건': 'ITEM',
        '장소': 'LOCATION',
        '사건': 'EVENT'
    }
    db_category = category_map.get(category, 'CHARACTER') # 기본값은 인물

    # 현재 폴더 위치 파악
    current_folder = request.GET.get('folder', '/')
    if not current_folder.endswith('/'):
        current_folder += '/'

    if request.method == "POST":
        name = request.POST.get("name")
        keyword_name = request.POST.get("keyword_name")
        
        if name and keyword_name:
            # 뼈대(StoryElement) 생성
            new_element = StoryElement.objects.create(
                author=request.user,
                novel=novel,
                category=db_category,
                name=name,
                keyword_name=keyword_name,
                folder_path=current_folder
            )
            
            # 자식 테이블 생성 및 상세 데이터 저장
            if db_category == 'CHARACTER':
                CharacterDetail.objects.create(
                    element=new_element,
                    aliases=request.POST.get("aliases", ""),
                    weapon=request.POST.get("weapon", ""),
                    personality=request.POST.get("personality", ""),
                    appearance=request.POST.get("appearance", ""),
                    taboo=request.POST.get("taboo", "")
                )
            elif db_category == 'FACTION':
                FactionDetail.objects.create(
                    element=new_element,
                    alignment=request.POST.get("alignment", ""),
                    base_location=request.POST.get("base_location", ""),
                    ideology=request.POST.get("ideology", ""),
                    key_members=request.POST.get("key_members", "")
                )
            elif db_category == 'ITEM':
                ItemDetail.objects.create(
                    element=new_element,
                    item_type=request.POST.get("item_type", ""),
                    appearance=request.POST.get("appearance", ""),
                    effect=request.POST.get("effect", ""),
                    penalty=request.POST.get("penalty", "")
                )
            elif db_category == 'LOCATION':
                LocationDetail.objects.create(
                    element=new_element,
                    region=request.POST.get("region", ""),
                    ruler=request.POST.get("ruler", ""),
                    climate=request.POST.get("climate", ""),
                    significance=request.POST.get("significance", "")
                )
            elif db_category == 'EVENT':
                EventDetail.objects.create(
                    element=new_element,
                    timeline=request.POST.get("timeline", ""),
                    participants=request.POST.get("participants", ""),
                    trigger=request.POST.get("trigger", ""),
                    impact=request.POST.get("impact", "")
                )
                
            # 새로고침
            return redirect(f"{reverse('world_element_list', args=[novel.id, category])}?folder={current_folder}")

    # 가상 폴더 탐색기 로직
    all_elements = StoryElement.objects.filter(novel=novel, category=db_category, is_deleted=False).order_by('-created_at')
    
    sub_folders = set()
    elements_in_folder = []

    for el in all_elements:
        if el.folder_path.startswith(current_folder):
            # 현재 폴더 경로를 잘라내고 남은 뒷부분 확인
            remainder = el.folder_path[len(current_folder):]
            if remainder:
                # 하위 폴더가 더 있다면 폴더 이름만 추출 (예: '화산파/장문인/' -> '화산파')
                next_folder = remainder.split('/')[0]
                sub_folders.add(next_folder)
            else:
                if el.name != "__FOLDER_DUMMY__":
                    elements_in_folder.append(el)

    return render(request, "world_element_list.html", {
        "novel": novel,
        "category": category,
        "elements": elements_in_folder,
        "sub_folders": sorted(list(sub_folders)), # 템플릿에 하위 폴더 리스트 전달
        "current_folder": current_folder,         # 현재 경로 전달
    })


@login_required
def world_element_detail_view(request, novel_id, category, element_id):
    novel = get_object_or_404(Novel, id=novel_id, author=request.user)
    element = get_object_or_404(StoryElement, id=element_id, novel=novel, author=request.user, is_deleted=False)
    
    detail = None
    if element.category == 'CHARACTER' and hasattr(element, 'character_detail'):
        detail = element.character_detail
    elif element.category == 'FACTION' and hasattr(element, 'faction_detail'):
        detail = element.faction_detail
    elif element.category == 'ITEM' and hasattr(element, 'item_detail'):
        detail = element.item_detail
    elif element.category == 'LOCATION' and hasattr(element, 'location_detail'):
        detail = element.location_detail
    elif element.category == 'EVENT' and hasattr(element, 'event_detail'):
        detail = element.event_detail
    
    # POST 요청: '저장하기' 버튼을 눌렀을 때 데이터 업데이트
    if request.method == "POST":
        # 기본 뼈대 업데이트 (이름, 키워드)
        element.name = request.POST.get("name", element.name)
        element.keyword_name = request.POST.get("keyword_name", element.keyword_name)
        element.save()

        # 카테고리별 세부 데이터 업데이트
        if element.category == 'CHARACTER' and detail:
            detail.aliases = request.POST.get("aliases", detail.aliases)
            detail.birthday = request.POST.get("birthday", detail.birthday)
            detail.main_skill = request.POST.get("main_skill", detail.main_skill)
            detail.level = request.POST.get("level", detail.level)
            detail.weapon = request.POST.get("weapon", detail.weapon)
            detail.clothing = request.POST.get("clothing", detail.clothing)
            detail.personality = request.POST.get("personality", detail.personality)
            detail.desire = request.POST.get("desire", detail.desire)
            detail.appearance = request.POST.get("appearance", detail.appearance)
            detail.taboo = request.POST.get("taboo", detail.taboo)
            detail.allies = request.POST.get("allies", detail.allies)
            detail.enemies = request.POST.get("enemies", detail.enemies)
            detail.save()
            
        elif element.category == 'FACTION' and detail:
            detail.alignment = request.POST.get("alignment", detail.alignment)
            detail.base_location = request.POST.get("base_location", detail.base_location)
            detail.ideology = request.POST.get("ideology", detail.ideology)
            detail.hierarchy = request.POST.get("hierarchy", detail.hierarchy)
            detail.key_members = request.POST.get("key_members", detail.key_members)
            detail.assets = request.POST.get("assets", detail.assets)
            detail.save()
            
        elif element.category == 'ITEM' and detail:
            detail.item_type = request.POST.get("item_type", detail.item_type)
            detail.appearance = request.POST.get("appearance", detail.appearance)
            detail.effect = request.POST.get("effect", detail.effect)
            detail.penalty = request.POST.get("penalty", detail.penalty)
            detail.origin = request.POST.get("origin", detail.origin)
            detail.save()
            
        elif element.category == 'LOCATION' and detail:
            detail.region = request.POST.get("region", detail.region)
            detail.ruler = request.POST.get("ruler", detail.ruler)
            detail.climate = request.POST.get("climate", detail.climate)
            detail.significance = request.POST.get("significance", detail.significance)
            detail.hidden_history = request.POST.get("hidden_history", detail.hidden_history)
            detail.save()
            
        elif element.category == 'EVENT' and detail:
            detail.timeline = request.POST.get("timeline", detail.timeline)
            detail.participants = request.POST.get("participants", detail.participants)
            detail.trigger = request.POST.get("trigger", detail.trigger)
            detail.impact = request.POST.get("impact", detail.impact)
            detail.save()

        # 저장 후 현재 페이지 새로고침
        return redirect('world_element_detail', novel_id=novel.id, category=category, element_id=element.id)

    return render(request, "world_element_detail.html", {
        "novel": novel,
        "category": category,
        "element": element,
        "detail": detail
    })


@login_required
def novel_settings_view(request, novel_id):
    novel = get_object_or_404(Novel, id=novel_id, author=request.user)
    
    if request.method == "POST":
        novel.title = request.POST.get("title", novel.title)
        novel.description = request.POST.get("description", novel.description)
        novel.save()

        return redirect('world_category', novel_id=novel.id)

    return render(request, "novel_settings.html", {
        "novel": novel
    })


@login_required
def world_element_delete_view(request, novel_id, category, element_id):
    if request.method == "POST":
        novel = get_object_or_404(Novel, id=novel_id, author=request.user)
        element = get_object_or_404(StoryElement, id=element_id, novel=novel, author=request.user)
        
        # 안전 삭제: DB에는 남겨두고 삭제된 것처럼 처리
        element.is_deleted = True
        element.save()
        
    return redirect('world_element_list', novel_id=novel.id, category=category)


# views.py 가장 아래에 추가

@login_required
def create_novel(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description", "")
        if title:
            # 현재 로그인한 작가의 소설로 DB에 완전 새로 생성
            Novel.objects.create(
                title=title, 
                description=description, 
                author=request.user
            )
    return redirect('world_list') # 대시보드로 새로고침


@login_required
def delete_novel(request, novel_id):
    if request.method == "POST":
        novel = get_object_or_404(Novel, id=novel_id, author=request.user)
        # 소설은 완전 삭제(Hard Delete) 적용
        novel.delete()
    return redirect('world_list')


@login_required
def world_element_bulk_action(request, novel_id, category):
    if request.method == "POST":
        novel = get_object_or_404(Novel, id=novel_id, author=request.user)
        
        # 프론트엔드에서 넘겨줄 데이터들
        action = request.POST.get("action") # 'delete', 'duplicate', 'move'
        current_folder = request.POST.get("current_folder", "/")

        is_folder_action = request.POST.get("is_folder_action") == "true"

        if is_folder_action:
            action_target_folder = request.POST.get("action_target_folder") # 조작할 폴더 전체 경로 (예: /화산파/)
            category_map = {'인물': 'CHARACTER', '단체': 'FACTION', '물건': 'ITEM', '장소': 'LOCATION', '사건': 'EVENT'}
            db_category = category_map.get(category, 'CHARACTER')
            
            # 해당 폴더 경로로 시작하는 모든 요소를 싹 다 선택
            elements_in_folder = StoryElement.objects.filter(
                novel=novel, author=request.user, category=db_category, 
                folder_path__startswith=action_target_folder, is_deleted=False
            )
            
            if action == "delete":
                elements_in_folder.update(is_deleted=True)
            elif action == "move":
                target_folder = request.POST.get("target_folder", "/")
                # 하위 요소들의 경로를 일괄 업데이트 하는 로직 (복잡도를 낮추기 위해 우선 단순 이동 처리)
                for el in elements_in_folder:
                    new_path = el.folder_path.replace(action_target_folder, target_folder, 1)
                    el.folder_path = new_path
                    el.save()
                    
            return redirect(f"{reverse('world_element_list', args=[novel.id, category])}?folder={current_folder}")


        element_ids = request.POST.getlist("element_ids")
        target_folder = request.POST.get("target_folder", "/")
        elements = StoryElement.objects.filter(id__in=element_ids, novel=novel, author=request.user)
        
        if action == "delete":
            elements.update(is_deleted=True)
        elif action == "move":
            elements.update(folder_path=target_folder)
        elif action == "duplicate":
            for el in elements:
                new_el = StoryElement.objects.create(
                    author=el.author, novel=el.novel, category=el.category,
                    folder_path=el.folder_path, name=f"{el.name} - 복사본", keyword_name=el.keyword_name
                )
                if el.category == 'CHARACTER' and hasattr(el, 'character_detail'):
                    d = el.character_detail
                    CharacterDetail.objects.create(
                        element=new_el, aliases=d.aliases, birthday=d.birthday, appearance=d.appearance, clothing=d.clothing,
                        main_skill=d.main_skill, level=d.level, weapon=d.weapon, personality=d.personality, desire=d.desire, taboo=d.taboo, allies=d.allies, enemies=d.enemies
                    )
                elif el.category == 'FACTION' and hasattr(el, 'faction_detail'):
                    d = el.faction_detail
                    FactionDetail.objects.create(
                        element=new_el, alignment=d.alignment, ideology=d.ideology, hierarchy=d.hierarchy, key_members=d.key_members, base_location=d.base_location, assets=d.assets
                    )
                elif el.category == 'ITEM' and hasattr(el, 'item_detail'):
                    d = el.item_detail
                    ItemDetail.objects.create(
                        element=new_el, item_type=d.item_type, appearance=d.appearance, effect=d.effect, penalty=d.penalty, origin=d.origin
                    )
                elif el.category == 'LOCATION' and hasattr(el, 'location_detail'):
                    d = el.location_detail
                    LocationDetail.objects.create(
                        element=new_el, region=d.region, climate=d.climate, ruler=d.ruler, significance=d.significance, hidden_history=d.hidden_history
                    )
                elif el.category == 'EVENT' and hasattr(el, 'event_detail'):
                    d = el.event_detail
                    EventDetail.objects.create(
                        element=new_el, timeline=d.timeline, participants=d.participants, trigger=d.trigger, impact=d.impact
                    )

    # 작업 완료 후, 머물러 있던 현재 폴더 위치로 돌아감
    return redirect(f"{reverse('world_element_list', args=[novel.id, category])}?folder={current_folder}")