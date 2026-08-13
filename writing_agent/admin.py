from django.contrib import admin
from .models import (
    AuthorProfile, Novel, StoryElement,
    CharacterDetail, FactionDetail, ItemDetail, LocationDetail, EventDetail
)

@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'originality_point')
    search_fields = ('user__username',)


@admin.register(Novel)
class NovelAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    list_filter = ('author',)
    search_fields = ('title',)


class CharacterDetailInline(admin.StackedInline):
    model = CharacterDetail
    can_delete = False

class FactionDetailInline(admin.StackedInline):
    model = FactionDetail
    can_delete = False

class ItemDetailInline(admin.StackedInline):
    model = ItemDetail
    can_delete = False

class LocationDetailInline(admin.StackedInline):
    model = LocationDetail
    can_delete = False

class EventDetailInline(admin.StackedInline):
    model = EventDetail
    can_delete = False

@admin.register(StoryElement)
class StoryElementAdmin(admin.ModelAdmin):
    # 폴더 경로(folder_path)와 키워드(keyword_name)를 띄움
    list_display = ('name', 'category', 'novel', 'folder_path', 'author', 'created_at')
    
    # 우측 폴더링 필터
    list_filter = ('novel', 'category', 'folder_path', 'author') 
    
    # 검색창 활성화
    search_fields = ('name', 'keyword_name', 'folder_path')
    
    # 모델 필드 구조에 맞게 에디터 화면 조정
    fieldsets = (
        ('기본 인덱스 정보', {
            'fields': ('author', 'novel', 'folder_path', 'category', 'name', 'keyword_name')
        }),
        ('상태 및 권한', {
            'fields': ('is_deleted',),
            'classes': ('collapse',),
        }),
    )

    inlines = [
        CharacterDetailInline,
        FactionDetailInline,
        ItemDetailInline,
        LocationDetailInline,
        EventDetailInline
    ]

# 새로 만든 5개의 세부 확장 테이블도 어드민에서 관리할 수 있도록 기본 등록
admin.site.register(CharacterDetail)
admin.site.register(FactionDetail)
admin.site.register(ItemDetail)
admin.site.register(LocationDetail)
admin.site.register(EventDetail)