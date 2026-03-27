from django.urls import path, re_path
from .views import iframe_, review_form, manual_review_form, public_reviews, user_reviews_api, reply_to_negative_review

urlpatterns = [
    re_path(r'^widget/iframe/(?P<user_id>[0-9a-f-]+)/?$', iframe_, name='iframe_widget'),
    path('review/<uuid:token>/', review_form, name='review_form'),
    path('manual-review/', manual_review_form, name='manual_review_form'),
    path('public-reviews/<uuid:user_id>/', public_reviews, name='public_reviews'),
    path('my-reviews/', user_reviews_api, name='user_reviews_api'),
    path('reply-to-negative/<uuid:review_id>/', reply_to_negative_review, name='reply_to_negative_review'),
]