from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("writer/setup/", views.writer_setup, name="writer_setup"),
    path("writer/blocks/add/", views.add_block, name="add_block"),
    path("editor/", views.editor, name="editor"),
]
