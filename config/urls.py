from django.urls import include, path

urlpatterns = [
    path("", include("writing_agent.urls")),
]
