import os

import requests
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from dotenv import load_dotenv
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
                             IsStaffAdminOrReadOnly,
                             IsStaffOrAdmin)
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


load_dotenv()

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
    permission_classes = (AllowAny,)  # (IsAdminOrSuperuser,)
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
    permission_classes = (AllowAny,)  # (IsStaffAdminOrReadOnly,)
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

    @action(detail=True, methods=['get', 'post'])
    def sessions(self, request, pk=None):
        quiz = self.get_object()
        sessions = QuizSession.objects.filter(quiz=quiz)
        serializer = QuizSessionSerializer(sessions, many=True)
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
    permission_classes = (AllowAny,)  # (IsStaffAdminOrReadOnly,)
    serializer_class = QuestionSerializer

    @action(detail=True, methods=['get'])
    def answers(self, request, pk=None):
        answers = Answer.objects.filter(question_id=pk)
        serializer = AnswerSerializer(answers, many=True)
        return Response(serializer.data)


class AnswerViewSet(viewsets.ModelViewSet):
    """Answer model view set."""
    queryset = Answer.objects.all()
    permission_classes = (AllowAny,)  # (IsStaffAdminOrReadOnly,)
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
        if not self.request.user.is_authenticated:
            raise PermissionDenied("User must be authenticated to create a session.")
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def calculate_score(self, request, pk=None):
        """
        Calculates the score for the given quiz session.
        """
        try:
            session = self.get_object()  # Get the specific QuizSession instance
            session.calculate_score()
            """session.save()  # Ensure to save the updated score to the database
            serializer = self.get_serializer(session)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except QuizSession is None:
            return Response({'error': 'Quiz session not found'}, status=status.HTTP_404_NOT_FOUND)"""
            return Response({'status': 'score calculated'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResponseViewSet(viewsets.ModelViewSet):
    """Response model view set."""
    queryset = UserResponse.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = (AllowAny,)  # (IsAuthenticated,)

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


class QuizListView(APIView):
    """Lists all available quizzes for regular users."""
    def get(self, request, *args, **kwargs):
        response = requests.get(f'{settings.API_BASE_URL}quizzes/')
        if response.status_code == status.HTTP_200_OK:
            quizzes = response.json()
            return render(request, 'quiz/quiz_list.html', {'quizzes': quizzes})
        return Response({'detail': 'Unable to retrieve quizzes.'}, status=response.status_code)


class TakeQuizView(APIView):
    """Allows authenticated users to take a quiz and submit responses."""
    permission_classes = (AllowAny,)

    def get(self, request, quiz_id):
        # Fetch the quiz details
        response = requests.get(f'{settings.API_BASE_URL}quizzes/{quiz_id}/')
        if response.status_code == status.HTTP_200_OK:
            quiz = response.json()
            # Fetch the details of each question
            questions = []
            for question_url in quiz['questions']:
                question_response = requests.get(question_url)
                if question_response.status_code == status.HTTP_200_OK:
                    question = question_response.json()
                    questions.append(question)

            quiz['questions'] = questions  # Replace URLs with question details
            return render(request, 'quiz/take_quiz.html', {'quiz': quiz})

        return redirect('quiz_list')

    def post(self, request, quiz_id):
        # Collecting quiz taker responses from the form
        answer_ids = request.POST.getlist('responses')  # Get all selected response IDs
        answers = []
        for answer_id in answer_ids:
            answer_response = requests.get(f'{settings.API_BASE_URL}answers/{answer_id}/')
            if answer_response.status_code == status.HTTP_200_OK:
                answers.append(answer_response.json())
        # Fetching the quiz object to get the questions
        quiz_response = requests.get(f'{settings.API_BASE_URL}quizzes/{quiz_id}/')
        if quiz_response.status_code != status.HTTP_200_OK:
            return Response(quiz_response.json(), status=quiz_response.status_code)
        quiz = quiz_response.json()
        # Creating the quiz session
        session_data = {'quiz': quiz_id}
        headers = {
            'Authorization': f'{os.getenv("JWT_TOKEN")}',
            # Adjust according to your authentication scheme
        }
        session_response = requests.post(f'{settings.API_BASE_URL}sessions/', json=session_data, headers=headers)
        if session_response.status_code != status.HTTP_201_CREATED:
            return Response(session_response.json(), status=session_response.status_code)

        session_id = session_response.json().get('id')
        # Iterate through responses and create Response objects
        response_errors = []
        for answer in answers:
            # Create the Response object
            response_data = {
                'session': session_id,
                'question': answer['question'],
                'selected_answer': answer['id']
            }
            response = requests.post(f'{settings.API_BASE_URL}responses/', json=response_data, headers=headers)
            if response.status_code != status.HTTP_201_CREATED:
                response_errors.append(response.json())
        # Trigger the calculate_score endpoint of the quiz session api
        calculate_score_url = f'{settings.API_BASE_URL}sessions/{session_id}/calculate_score/'
        calculate_score_response = requests.post(calculate_score_url, headers=headers)
        if calculate_score_response.status_code != status.HTTP_200_OK:
            return Response({'errors': ['Failed to calculate score']}, status=status.HTTP_400_BAD_REQUEST)

        if not response_errors:
            print(f"Redirecting to quiz_result with session_id: {session_id}")
            return redirect('quiz_result', session_id=session_id)
        return Response({'errors': response_errors}, status=status.HTTP_400_BAD_REQUEST)


class QuizResultView(APIView):
    """Displays the results of a completed quiz session."""
    permission_classes = (AllowAny,)

    def get(self, request, session_id):
        headers = {
            'Authorization': f'{os.getenv("JWT_TOKEN")}'
            # Adjust according to your authentication scheme
        }
        response = requests.get(f'{settings.API_BASE_URL}sessions/{session_id}/', headers=headers)
        session = response.json()
        quiz_response = requests.get(f'{settings.API_BASE_URL}quizzes/{session["quiz"]}/', headers=headers)
        quiz = quiz_response.json()
        if response.status_code == status.HTTP_200_OK:
            session_data = response.json()
            print(session_data)
            return render(request,
                          'quiz/quiz_result.html',
                          {'session': session_data, 'quiz': quiz})
        return redirect('quiz_list')
