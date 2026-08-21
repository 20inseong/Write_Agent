from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Novel

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