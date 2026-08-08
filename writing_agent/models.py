from django.db import models

class StoryElement(models.Model):
    # 카테고리 정의
    CATEGORY_CHOICES = (
        ('CHARACTER', '인물'),
        ('FACTION', '단체'),
        ('ITEM', '물건'),
        ('LOCATION', '장소'),
        ('EVENT', '사건'),
    )
    
    # 데이터 필드
    name = models.CharField(max_length=100, verbose_name="명칭 (이름/제목)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="분류")
    keywords = models.CharField(max_length=255, verbose_name="매칭 키워드 (쉼표로 구분)")
    summary = models.CharField(max_length=200, verbose_name="한 줄 요약")
    content = models.TextField(verbose_name="AI에게 주입될 상세 문맥(Context)")

    def __str__(self):
        # 어드민 리스트에서 "[인물] 강무현", "[단체] 해남파" 형태로 보이게 함
        return f"[{self.get_category_display()}] {self.name}"