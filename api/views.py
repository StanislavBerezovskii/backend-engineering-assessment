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
                             SignUpSerializer,
                             TokenSerializer,
                             UserSerializer)
from quiz.models import Answer, Question, Quiz
from users.models import User


API_BASE_URL = getattr(settings, 'API_BASE_URL', 'http://127.0.0.1:8000/api/')


class SignUpView(APIView):
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


class IndexView(APIView):
    """Demo view function for development. Shows all available Quizzes."""
    def get(self, request):
        api_url = f"{settings.API_BASE_URL}quizzes/"
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            quizzes = response.json()
        except requests.RequestException as e:
            # Log the error or handle it as needed
            quizzes = []
            print(f"Error fetching quizzes: {e}")

        return render(request, 'index.html', {'quizzes': quizzes})


class SessionView(APIView):
    def get(self, request, quiz_id):
        # API URL for fetching questions
        api_url = f"{settings.API_BASE_URL}quizzes/{quiz_id}/get_all_questions/"
        response = requests.get(api_url)

        if response.status_code == 200:
            questions = response.json()
        else:
            return render(request, 'error.html', {'message': 'Error fetching questions'})

        # Initialize session variables if not already set
        if 'current_question_index' not in request.session:
            request.session['current_question_index'] = 0
            request.session['user_answers'] = []

        current_index = request.session['current_question_index']
        if current_index < len(questions):
            question = questions[current_index]
        else:
            # Quiz finished, calculate results
            return self.calculate_results(request, questions)

        return render(request, 'session.html', {'question': question, 'quiz_id': quiz_id})

    def post(self, request, quiz_id):
        selected_answer_id = request.data.get('answer_id')
        if not selected_answer_id:
            return render(request, 'error.html', {'message': 'No answer selected'})

        # Store the selected answer
        request.session['user_answers'].append(selected_answer_id)
        request.session['current_question_index'] += 1

        return redirect('session', quiz_id=quiz_id)

    def calculate_results(self, request, questions):
        correct_answers_count = 0
        total_questions = len(questions)

        # Check user's selected answers
        for i, question in enumerate(questions):
            selected_answer_id = request.session['user_answers'][i]
            api_url = f"{settings.API_BASE_URL}/answers/{selected_answer_id}/"
            response = requests.get(api_url)

            if response.status_code == 200:
                answer = response.json()
                if answer.get('is_correct'):
                    correct_answers_count += 1

        # Clear session data
        del request.session['current_question_index']
        del request.session['user_answers']

        return render(request, 'results.html', {
            'correct_answers_count': correct_answers_count,
            'total_questions': total_questions
        })


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
            permission_classes= (AllowAny,),)  #(IsAuthenticated,),)
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

    @action(detail=True, methods=['get'])
    def get_all_questions(self, request, pk=None):
        quiz = self.get_object()
        questions = Question.objects.filter(quiz=quiz)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    permission_classes = (AllowAny,)  # (IsStaffAdminOrReadOnly,)
    serializer_class = QuestionSerializer

    @action(detail=True, methods=['get'])
    def answers(self, request, pk=None):
        answers = Answer.objects.filter(question_id=pk)
        serializer = AnswerSerializer(answers, many=True)
        return Response(serializer.data)


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    permission_classes = (AllowAny,)  # (IsStaffAdminOrReadOnly,)
    serializer_class = AnswerSerializer

    @property
    def paginator(self):
        self._paginator = None
