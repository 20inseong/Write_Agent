from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from ..forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from ..models import TemporaryDraft

def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "landing.html")


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

@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    has_temp_draft = False
    draft_updated_at = ""

    # 현재 로그인한 작가의 임시 저장 데이터가 있는지 조회 (가장 최근 것 1개)
    draft = TemporaryDraft.objects.filter(author=request.user, is_deleted=False).order_by('-updated_at').first()
    
    if draft and (draft.user_content or draft.ai_draft_content):
        has_temp_draft = True
        draft_updated_at = draft.updated_at.strftime('%m/%d %H:%M')

    return render(request, "dashboard.html", {
        "has_temp_draft": has_temp_draft,
        "draft_updated_at": draft_updated_at
    })