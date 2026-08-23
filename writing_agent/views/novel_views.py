from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Novel, Episode, TemporaryDraft, AuthorProfile

@login_required
def world_list_view(request):
    my_novels = Novel.objects.filter(author=request.user)
    return render(request, "world_list.html", {"novels": my_novels})

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
def settings_archive_view(request):
    # 작가(로그인 유저)에 종속된 데이터만 격리 조회 및 소프트 딜리트 필터링 적용
    my_novels = Novel.objects.filter(author=request.user).exclude(title='[자유 창작 노트 (기본)]')
    my_episodes = Episode.objects.filter(author=request.user, is_deleted=False).order_by('-updated_at')
    my_drafts = TemporaryDraft.objects.filter(author=request.user, is_deleted=False).order_by('-updated_at')
    
    # 뱃지 및 스탯 관리를 위한 프로필 조회 (없으면 자동 생성)
    author_profile, _ = AuthorProfile.objects.get_or_create(user=request.user)

    return render(request, "settings.html", {
        "novels": my_novels,
        "episodes": my_episodes,
        "drafts": my_drafts,
        "profile": author_profile,
    })

@login_required
def episode_viewer_view(request, episode_id):
    # 보안: 로그인한 작가 본인의 글인지 확인 + 논리적 삭제(소프트 딜리트)되지 않은 글인지 확인
    episode = get_object_or_404(Episode, id=episode_id, author=request.user, is_deleted=False)
    
    return render(request, "viewer.html", {
        "episode": episode
    })