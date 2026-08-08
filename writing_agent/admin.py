from django.contrib import admin
from .models import StoryElement

@admin.register(StoryElement)
class StoryElementAdmin(admin.ModelAdmin):
    # 어드민 게시판 목록에 보여줄 항목들
    list_display = ('name', 'category', 'summary')
    
    # 우측에 '분류별(인물, 단체 등) 모아보기' 필터 패널 생성
    list_filter = ('category',)
    
    # 검색창 활성화: 명칭이나 키워드로 쉽게 데이터를 찾을 수 있게 함
    search_fields = ('name', 'keywords')