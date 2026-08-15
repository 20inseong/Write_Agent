from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("writer/blocks/add/", views.add_block, name="add_block"),

    # 자유 창작용
    path("writer/setup/", views.writer_setup, name="writer_setup"),
    path("editor/", views.editor, name="editor"),
    
    # 세계관 창작용
    path("writer/setup/world/", views.world_list_view, name="world_list"),
    path("world/<int:novel_id>/", views.world_category_view, name="world_category"),
    path("world/<int:novel_id>/settings/", views.novel_settings_view, name="novel_settings"),
    path("world/<int:novel_id>/<str:category>/", views.world_element_list_view, name="world_element_list"),
    path("world/<int:novel_id>/<str:category>/<uuid:element_id>/", views.world_element_detail_view, name="world_element_detail"),

    path("world/<int:novel_id>/<str:category>/<uuid:element_id>/delete/", views.world_element_delete_view, name="world_element_delete"),

    # path("editor/world/<int:novel_id>/", views.world_editor, name="world_editor"),
]
