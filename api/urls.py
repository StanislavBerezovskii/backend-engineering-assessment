from django.urls import include, path
from rest_framework import routers

from api.views import (IndexView,
                       SessionView,
                       AnswerViewSet,
                       QuestionViewSet,
                       QuizViewSet,
                       SignUpView,
                       TokenView,
                       UserViewSet)

router = routers.SimpleRouter()
router.register(r'answers', AnswerViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/signup/', SignUpView.as_view()),
    path('auth/token/', TokenView.as_view()),
    path('index/', IndexView.as_view(), name='index'),
    path('session/<int:quiz_id>/', SessionView.as_view(), name='session'),
]
