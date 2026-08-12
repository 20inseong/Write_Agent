from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from writing_agent import views as agent_views
from writing_agent.forms import CustomLoginForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("writing_agent.urls")),
    path('signup/', agent_views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', authentication_form=CustomLoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]
