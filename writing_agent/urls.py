from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("writer/blocks/add/", views.add_block, name="add_block"),

    # 자유 창작용
    path("writer/setup/", views.writer_setup, name="writer_setup"),
    path("editor/", views.editor, name="editor"),
    
    # 세계관 글쓰기용
    path("writer/setup/<int:novel_id>/", views.writer_setup, name="writer_setup_with_id"),
    path("editor/<int:novel_id>/", views.editor, name="editor_with_id"),
    path('api/verify-keywords/<int:novel_id>/', views.verify_keywords_api, name='verify_keywords_api'),

    # API 통신용
    path('api/verify-keywords/<int:novel_id>/', views.verify_keywords_api, name='verify_keywords_api'),
    path('api/generate-block/', views.generate_single_block_api, name='generate_single_block_api_free'),
    path('api/generate-block/<int:novel_id>/', views.generate_single_block_api, name='generate_single_block_api'),

    # 세계관 DB 이용
    path("writer/setup/world/", views.world_list_view, name="world_list"),
    path("world/<int:novel_id>/", views.world_category_view, name="world_category"),
    path("world/<int:novel_id>/settings/", views.novel_settings_view, name="novel_settings"),
    path("world/<int:novel_id>/<str:category>/", views.world_element_list_view, name="world_element_list"),
    path("world/<int:novel_id>/<str:category>/<uuid:element_id>/", views.world_element_detail_view, name="world_element_detail"),
    path("world/<int:novel_id>/<str:category>/<uuid:element_id>/delete/", views.world_element_delete_view, name="world_element_delete"),

    path('world/create/', views.create_novel, name='create_novel'),
    path('world/delete/<int:novel_id>/', views.delete_novel, name='delete_novel'),
    path('world/element_action/<int:novel_id>/<str:category>/', views.world_element_bulk_action, name='world_element_bulk_action'),

    path('api/save_draft/', views.save_temp_draft, name='save_temp_draft'),
]
