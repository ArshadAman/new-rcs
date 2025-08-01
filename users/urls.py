from django.urls import path
from .views import signup_view, profile_view, update_profile_view

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('profile/', profile_view, name='profile'),
    path('profile/update/', update_profile_view, name='update_profile'),
]