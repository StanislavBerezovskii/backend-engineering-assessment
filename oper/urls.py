from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from api.urls import urlpatterns as api_urlpatterns
from api.views import QuizListView, TakeQuizView, QuizResultView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),
    path('quizzes/', QuizListView.as_view(), name='quiz_list'),
    path('quizzes/<int:quiz_id>/take/', TakeQuizView.as_view(), name='take_quiz'),
    path('sessions/<int:session_id>/result/', QuizResultView.as_view(), name='quiz_result'),
]
