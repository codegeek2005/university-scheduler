from django.urls import path
from django.contrib.auth import views as auth_views
from .views import api, web 

urlpatterns = [
    # --- AUTHENTICATION ---
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('signup/', web.signup, name='signup'),

    # --- API ENDPOINTS (The Engine) ---
    path('api/v1/generate-schedule/', api.GenerateScheduleView.as_view(), name='generate_schedule'),
    
    # --- PUBLIC PORTAL ROUTES ---
    path('', web.home, name='home'),
    path('student/', web.student_dashboard, name='student_dashboard'),
    path('faculty/', web.teacher_dashboard, name='teacher_dashboard'),
    path('coordinator/', web.coordinator_dashboard, name='coordinator_dashboard'),
    path('timetable/', web.master_timetable, name='master_timetable'),
]