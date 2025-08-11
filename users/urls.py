from django.urls import path
from .views import signup_view, profile_view, update_profile_view, user_statistics_api

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('profile/', profile_view, name='profile'),
    path('profile/update/', update_profile_view, name='update_profile'),
     path('statistics/', user_statistics_api, name='user_statistics_api'),
]