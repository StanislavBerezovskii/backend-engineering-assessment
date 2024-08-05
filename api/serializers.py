from django.conf import settings
from rest_framework import serializers

from quiz.models import Answer, Question, Quiz
from users.models import User
from users.validators import validate_username


class SignUpSerializer(serializers.Serializer):
    """User registration serializer."""

    username = serializers.CharField(max_length=settings.MAX_USERNAME_LENGTH)
    email = serializers.EmailField(max_length=settings.MAX_EMAIL_LENGTH)

    def validate_username(self, value):
        """Check if username is valid."""
        validate_username(value)
        return value


class TokenSerializer(serializers.Serializer):
    """Token serializer."""
    username = serializers.CharField(max_length=settings.MAX_USERNAME_LENGTH)
    confirmation_code = serializers.CharField(required=True)


class UserSerializer(serializers.ModelSerializer):
    """User model serializer."""

    class Meta:
        model = User
        fields = ['username',
                  'email',
                  'first_name',
                  'last_name',
                  'bio',
                  'role',]


class QuizSerializer(serializers.ModelSerializer):
    """Quiz model serializer."""
    questions = serializers.HyperlinkedRelatedField(many=True,
                                                    read_only=True,
                                                    view_name='question-detail')

    def getFullName(self, obj):
        """Get full name of user who created the quiz."""
        if obj.author:
            return f"{obj.author.first_name or ''} {obj.author.last_name or ''}".strip()
        return 'Unknown'

    def getQuestionCount(self, obj):
        """Get number of questions in the quiz."""
        return obj.questions.count()

    author_full_name = serializers.SerializerMethodField('getFullName')
    question_count = serializers.SerializerMethodField('getQuestionCount')

    class Meta:
        model = Quiz
        fields = ['id',
                  'title',
                  'author',
                  'author_full_name',
                  'question_count',
                  'created_at',
                  'questions']


class AnswerSerializer(serializers.ModelSerializer):
    """Answer model serializer."""
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())

    class Meta:
        model = Answer
        fields = ['id',
                  'question',
                  'answer_text',
                  'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    """Question model serializer."""
    quiz = serializers.PrimaryKeyRelatedField(queryset=Quiz.objects.all())
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id',
                  'quiz',
                  'quiz_title',
                  'prompt',
                  'answers']
