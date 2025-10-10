from django.urls import path
from .views import signup_view, profile_view, update_profile_view, user_statistics_api, user_plan_info, check_email_view

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('check-email/', check_email_view, name='check_email'),
    path('profile/', profile_view, name='profile'),
    path('profile/update/', update_profile_view, name='update_profile'),
    path('statistics/', user_statistics_api, name='user_statistics_api'),
    path('user-plan-info/', user_plan_info, name='user_plan_info'),
]