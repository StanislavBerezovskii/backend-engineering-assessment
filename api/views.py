import requests
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import (viewsets,
                            status)
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from api.permissions import (IsAdminOrSuperuser,
                             IsAdminSuperuserOrReadOnly,
                             IsStaffAdminOrReadOnly)
from api.serializers import (AnswerSerializer,
                             QuestionSerializer,
                             QuizSerializer,
                             QuizSessionSerializer,
                             ResponseSerializer,
                             SignUpSerializer,
                             TokenSerializer,
                             UserSerializer)
from quiz.models import Answer, Question, Quiz
from session.models import QuizSession, Response as UserResponse
from users.models import User


API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://127.0.0.1:8000/api/')


class SignUpView(APIView):
    """Handles user sign-up."""
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        username = serializer.validated_data['username']
        try:
            user, is_new = User.objects.get_or_create(
                email=email,
                username=username
            )
        except IntegrityError:
            raise ValidationError(detail='This username or email is already taken.')
        confirmation_code = default_token_generator.make_token(user)
        send_mail(subject='Signup confirmation',
                  message=f'Your confirmation code: "{confirmation_code}".',
                  from_email=settings.FROM_EMAIL,
                  recipient_list=(email,),)
        return Response({'email': email, 'username': username},
                        status=status.HTTP_200_OK,)


class TokenView(APIView):
    """Retrieves JWT-token for user."""
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirmation_code = serializer.validated_data.get('confirmation_code')
        username = serializer.validated_data.get('username')
        user = get_object_or_404(User, username=username)

        if default_token_generator.check_token(user, confirmation_code):
            user.is_active = True
            user.save()
            token = AccessToken.for_user(user)
            return Response({'token': f'{token}'}, status=status.HTTP_200_OK)

        return Response({'confirmation_code': ['Invalid confirmation code!']},
                        status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """User model view set."""
    queryset = User.objects.all()
    permission_classes = (IsAdminOrSuperuser,)
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = (SearchFilter,)
    search_fields = ('username',)

    @action(detail=False,
            methods=('GET', 'PATCH'),
            permission_classes=(IsAuthenticated,),)
    def me(self, request):
        serializer = UserSerializer(request.user)
        if request.method == 'PATCH':
            serializer = UserSerializer(
                request.user,
                data=request.data,
                partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
        return Response(serializer.data)


class QuizViewSet(viewsets.ModelViewSet):
    """Quiz model view set."""
    queryset = Quiz.objects.all()
    permission_classes = (IsStaffAdminOrReadOnly,)
    serializer_class = QuizSerializer

    @property
    def paginator(self):
        if getattr(self, '_paginator', None) is None:
            if self.action == 'questions':
                self._paginator = super().paginator
            else:
                self._paginator = None
        return self._paginator

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        quiz = self.get_object()
        questions = Question.objects.filter(quiz=quiz)
        paginator = self.paginator
        if paginator is not None:
            paginator.page_size = 1
        page = self.paginate_queryset(questions)
        if page is not None:
            serializer = QuestionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_all_questions(self, request, pk=None):
        quiz = self.get_object()
        questions = Question.objects.filter(quiz=quiz)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    """Question model view set."""
    queryset = Question.objects.all()
    permission_classes = (IsStaffAdminOrReadOnly,)
    serializer_class = QuestionSerializer

    @action(detail=True, methods=['get'])
    def answers(self, request, pk=None):
        answers = Answer.objects.filter(question_id=pk)
        serializer = AnswerSerializer(answers, many=True)
        return Response(serializer.data)


class AnswerViewSet(viewsets.ModelViewSet):
    """Answer model view set."""
    queryset = Answer.objects.all()
    permission_classes = (IsStaffAdminOrReadOnly,)
    serializer_class = AnswerSerializer

    @property
    def paginator(self):
        self._paginator = None


class QuizSessionViewSet(viewsets.ModelViewSet):
    """QuizSession model view set."""
    queryset = QuizSession.objects.all()
    serializer_class = QuizSessionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        Optionally restricts the returned quiz sessions to a given user,
        by filtering against a `user` query parameter in the URL.
        """
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        return queryset

    def perform_create(self, serializer):
        """
        Sets the user associated with the session to the current logged-in user.
        """
        serializer.save(user=self.request.user)


class ResponseViewSet(viewsets.ModelViewSet):
    """Response model view set."""
    queryset = UserResponse.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        Optionally restricts the returned responses to those related to a given session,
        by filtering against a `session` query parameter in the URL.
        """
        queryset = super().get_queryset()
        session_id = self.request.query_params.get('session_id')
        if session_id is not None:
            queryset = queryset.filter(session__id=session_id)
        return queryset

    def perform_create(self, serializer):
        """
        Sets additional data before creating a new response.
        """
        # Typically, the session and question are passed from the frontend
        serializer.save()
