from django.urls import include, path
from rest_framework import routers

from api.views import (SignUpView, TokenView,
                       AnswerViewSet, QuestionViewSet, QuizViewSet, QuizSessionViewSet, ResponseViewSet, UserViewSet)

router = routers.SimpleRouter()
router.register(r'answers', AnswerViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'sessions', QuizSessionViewSet)
router.register(r'responses', ResponseViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/signup/', SignUpView.as_view()),
    path('auth/token/', TokenView.as_view()),
]
