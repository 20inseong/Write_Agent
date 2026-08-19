from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from ..models import Novel, StoryElement, CharacterDetail, FactionDetail, ItemDetail, LocationDetail, EventDetail

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

            other_details = request.POST.get("other_details", "")
            
            # 자식 테이블 생성 및 상세 데이터 저장
            if db_category == 'CHARACTER':
                CharacterDetail.objects.create(
                    element=new_element,
                    aliases=request.POST.get("aliases", ""),
                    birthday=request.POST.get("birthday", ""),
                    main_skill=request.POST.get("main_skill", ""),
                    level=request.POST.get("level", ""),
                    weapon=request.POST.get("weapon", ""),
                    clothing=request.POST.get("clothing", ""),
                    personality=request.POST.get("personality", ""),
                    appearance=request.POST.get("appearance", ""),
                    desire=request.POST.get("desire", ""),
                    taboo=request.POST.get("taboo", ""),
                    allies=request.POST.get("allies", ""),
                    enemies=request.POST.get("enemies", ""),
                    other_details=other_details
                )
            elif db_category == 'FACTION':
                FactionDetail.objects.create(
                    element=new_element,
                    alignment=request.POST.get("alignment", ""),
                    base_location=request.POST.get("base_location", ""),
                    ideology=request.POST.get("ideology", ""),
                    hierarchy=request.POST.get("hierarchy", ""),
                    key_members=request.POST.get("key_members", ""),
                    assets=request.POST.get("assets", ""),
                    other_details=other_details
                )
            elif db_category == 'ITEM':
                ItemDetail.objects.create(
                    element=new_element,
                    item_type=request.POST.get("item_type", ""),
                    appearance=request.POST.get("appearance", ""),
                    effect=request.POST.get("effect", ""),
                    penalty=request.POST.get("penalty", ""),
                    origin=request.POST.get("origin", ""),
                    other_details=other_details
                )
            elif db_category == 'LOCATION':
                LocationDetail.objects.create(
                    element=new_element,
                    region=request.POST.get("region", ""),
                    ruler=request.POST.get("ruler", ""),
                    climate=request.POST.get("climate", ""),
                    significance=request.POST.get("significance", ""),
                    hidden_history=request.POST.get("hidden_history", ""),
                    other_details=other_details
                )
            elif db_category == 'EVENT':
                EventDetail.objects.create(
                    element=new_element,
                    timeline=request.POST.get("timeline", ""),
                    participants=request.POST.get("participants", ""),
                    trigger=request.POST.get("trigger", ""),
                    impact=request.POST.get("impact", ""),
                    other_details=other_details
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
            detail.other_details = request.POST.get("other_details", detail.other_details)
            detail.save()
            
        elif element.category == 'FACTION' and detail:
            detail.alignment = request.POST.get("alignment", detail.alignment)
            detail.base_location = request.POST.get("base_location", detail.base_location)
            detail.ideology = request.POST.get("ideology", detail.ideology)
            detail.hierarchy = request.POST.get("hierarchy", detail.hierarchy)
            detail.key_members = request.POST.get("key_members", detail.key_members)
            detail.assets = request.POST.get("assets", detail.assets)
            detail.other_details = request.POST.get("other_details", detail.other_details)
            detail.save()
            
        elif element.category == 'ITEM' and detail:
            detail.item_type = request.POST.get("item_type", detail.item_type)
            detail.appearance = request.POST.get("appearance", detail.appearance)
            detail.effect = request.POST.get("effect", detail.effect)
            detail.penalty = request.POST.get("penalty", detail.penalty)
            detail.origin = request.POST.get("origin", detail.origin)
            detail.other_details = request.POST.get("other_details", detail.other_details)
            detail.save()
            
        elif element.category == 'LOCATION' and detail:
            detail.region = request.POST.get("region", detail.region)
            detail.ruler = request.POST.get("ruler", detail.ruler)
            detail.climate = request.POST.get("climate", detail.climate)
            detail.significance = request.POST.get("significance", detail.significance)
            detail.hidden_history = request.POST.get("hidden_history", detail.hidden_history)
            detail.other_details = request.POST.get("other_details", detail.other_details)
            detail.save()
            
        elif element.category == 'EVENT' and detail:
            detail.timeline = request.POST.get("timeline", detail.timeline)
            detail.participants = request.POST.get("participants", detail.participants)
            detail.trigger = request.POST.get("trigger", detail.trigger)
            detail.impact = request.POST.get("impact", detail.impact)
            detail.other_details = request.POST.get("other_details", detail.other_details)
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
def world_element_delete_view(request, novel_id, category, element_id):
    if request.method == "POST":
        novel = get_object_or_404(Novel, id=novel_id, author=request.user)
        element = get_object_or_404(StoryElement, id=element_id, novel=novel, author=request.user)
        
        # 안전 삭제: DB에는 남겨두고 삭제된 것처럼 처리
        element.is_deleted = True
        element.save()
        
    return redirect('world_element_list', novel_id=novel.id, category=category)

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
        target_folder = request.POST.get("target_folder", "/").strip()
        if not target_folder.endswith('/'):
            target_folder += '/'

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

