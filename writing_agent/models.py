import uuid
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# 유저 스탯 테이블: 작가의 오리지널리티 점수와 뱃지를 독립적으로 관리
class AuthorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    originality_point = models.PositiveIntegerField(default=0, verbose_name="오리지널리티 누적 포인트")
    badges = models.JSONField(default=dict, blank=True, verbose_name="획득 뱃지 목록")

    def __str__(self):
        return f"{self.user.username} 작가 프로필"


class Novel(models.Model):
    title = models.CharField(max_length=200, verbose_name="소설 제목")
    description = models.TextField(blank=True, verbose_name="작품 소개")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="작가")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class StoryElement(models.Model):

    CATEGORY_CHOICES = (
        ('CHARACTER', '인물'),
        ('FACTION', '단체'),
        ('ITEM', '물건'),
        ('LOCATION', '장소'),
        ('EVENT', '사건'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='story_elements')
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, null=True, blank=True, related_name="elements")
    folder_path = models.CharField(max_length=255, default="/", verbose_name="폴더 경로")
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="분류")
    name = models.CharField(max_length=100, verbose_name="명칭 (객체 이름)")
    keyword_name = models.CharField(max_length=255, verbose_name="매칭 키워드 (쉼표 구분)")
    
    is_deleted = models.BooleanField(default=False, verbose_name="삭제 여부")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name}"


# 세부 확장 테이블
# 캐릭터(Character)
class CharacterDetail(models.Model):
    # 1:1 연결 고리
    element = models.OneToOneField(StoryElement, on_delete=models.CASCADE, related_name='character_detail')
    
    # [기본 정보]
    aliases = models.CharField(max_length=100, blank=True, verbose_name="이명/별호")
    birthday = models.CharField(max_length=100, blank=True, verbose_name="생일")
    
    # [외형 및 분위기]
    appearance = models.TextField(blank=True, verbose_name="첫인상 및 신체적 특징")
    clothing = models.CharField(max_length=200, blank=True, verbose_name="주요 복식")
    
    # [능력치]
    main_skill = models.CharField(max_length=200, blank=True, verbose_name="주력 능력/스킬")
    level = models.CharField(max_length=100, blank=True, verbose_name="현재 수준/경지")
    weapon = models.CharField(max_length=100, blank=True, verbose_name="주로 사용하는 것(무기, 물건)")
    
    # [성향 및 목표]
    personality = models.TextField(blank=True, verbose_name="성격 (장/단점)")
    desire = models.TextField(blank=True, verbose_name="궁극적인 욕망")
    taboo = models.TextField(blank=True, verbose_name="금기 (절대 하지 않을 행동)")
    
    # [관계망]
    allies = models.TextField(blank=True, verbose_name="우호 관계")
    enemies = models.TextField(blank=True, verbose_name="적대 관계")

    # [시스템 Hidden] AI 역산 사주 및 오행 데이터 전용 공간
    saju_meta = models.JSONField(default=dict, blank=True, verbose_name="사주/오행 메타 데이터")

    other_details = models.TextField(blank=True, null=True, verbose_name="기타 사항")


# 단체 및 세력 (FACTION)
class FactionDetail(models.Model):
    element = models.OneToOneField(StoryElement, on_delete=models.CASCADE, related_name='faction_detail')
    alignment = models.CharField(max_length=100, blank=True, verbose_name="세력 성향 (선악/정치적 스탠스)")
    ideology = models.TextField(blank=True, verbose_name="이념 및 창립 목적")
    hierarchy = models.TextField(blank=True, verbose_name="구조 및 위계 (수장, 서열)")
    key_members = models.TextField(blank=True, verbose_name="핵심 소속 인물")
    base_location = models.CharField(max_length=200, blank=True, verbose_name="본거지 위치")
    assets = models.TextField(blank=True, verbose_name="고유 기술, 자산 및 세력 규모")
    other_details = models.TextField(blank=True, null=True, verbose_name="기타 사항")

# 물건 (ITEM)
class ItemDetail(models.Model):
    element = models.OneToOneField(StoryElement, on_delete=models.CASCADE, related_name='item_detail')
    item_type = models.CharField(max_length=100, blank=True, verbose_name="분류 (소모품/아티팩트 등)")
    appearance = models.TextField(blank=True, verbose_name="외형 및 특유의 기운")
    effect = models.TextField(blank=True, verbose_name="효과 및 이점")
    penalty = models.TextField(blank=True, verbose_name="제약, 획득 조건 및 부작용")
    origin = models.TextField(blank=True, verbose_name="기원 및 이전 주인의 이야기")
    other_details = models.TextField(blank=True, null=True, verbose_name="기타 사항")

# 장소 (LOCATION)
class LocationDetail(models.Model):
    element = models.OneToOneField(StoryElement, on_delete=models.CASCADE, related_name='location_detail')
    region = models.CharField(max_length=100, blank=True, verbose_name="소속 지역")
    climate = models.TextField(blank=True, verbose_name="환경, 기후 및 지형적 특징")
    ruler = models.CharField(max_length=200, blank=True, verbose_name="지배 세력 또는 통치자")
    significance = models.TextField(blank=True, verbose_name="스토리적 상징성 (랜드마크)")
    hidden_history = models.TextField(blank=True, verbose_name="장소에 얽힌 숨겨진 역사")
    other_details = models.TextField(blank=True, null=True, verbose_name="기타 사항")

# 사건 (EVENT)
class EventDetail(models.Model):
    element = models.OneToOneField(StoryElement, on_delete=models.CASCADE, related_name='event_detail')
    timeline = models.CharField(max_length=100, blank=True, verbose_name="발생 시점 (과거/현재)")
    participants = models.TextField(blank=True, verbose_name="관련 주체 (인물 및 단체)")
    trigger = models.TextField(blank=True, verbose_name="발발 원인 및 전개 흐름")
    impact = models.TextField(blank=True, verbose_name="세계관에 미친 파급력 및 결과")
    other_details = models.TextField(blank=True, null=True, verbose_name="기타 사항")

    def __str__(self):
        return f"{self.element.name}의 상세 설정"