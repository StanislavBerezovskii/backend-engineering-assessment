from django.contrib import admin
from django.db.models import Q

from quiz.models import Answer, Question, Quiz


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Handles the Quiz model in the admin panel"""
    list_display = ['id', 'title', 'author', 'created_at']
    list_filter = ['author']
    search_fields = ['author', 'title']


class AnswerInline(admin.TabularInline):
    """Adds Answers to the Question model display in the admin panel"""
    model = Answer


class QuizQuestionFilter(admin.SimpleListFilter):
    """Filters the Question objects by related Quiz in the admin panel"""
    title = 'quiz'
    parameter_name = 'quiz'

    def lookups(self, request, model_admin):
        """Creates interactive links on the right side of the filter"""
        quizzes = Quiz.objects.all()
        lookups = ()
        for quiz in quizzes:
            lookups += ((quiz.title, quiz.title),)
        return lookups

    def queryset(self, request, queryset):
        """Returns all objects matching parameter"""
        if self.value():
            quiz_title = self.value()
            return queryset.filter(Q(quiz__title=quiz_title))


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Handles the Question model in the admin panel"""
    fields = ['prompt', 'quiz']
    list_display = ['id', 'prompt', 'quiz']
    list_filter = [QuizQuestionFilter]
    search_fields = ['quiz', 'title']
    inlines = [AnswerInline]


class AnswerQuestionFilter(admin.SimpleListFilter):
    """Filters the Answer objects by related Question in the admin panel"""
    title = 'question'
    parameter_name = 'question'

    def lookups(self, request, model_admin):
        """Creates interactive links on the right side of the filter"""
        questions = Question.objects.all()
        lookups = ()
        for question in questions:
            lookups += ((question.prompt, question.prompt),)
        return lookups

    def queryset(self, request, queryset):
        """Returns all objects matching parameter"""
        if self.value():
            question_prompt = self.value()
            return queryset.filter(question__prompt=question_prompt)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Handles the Answer model in the admin panel"""
    list_display = ['id', 'answer_text', 'is_correct', 'question']
    list_filter = [AnswerQuestionFilter]
    search_fields = [AnswerQuestionFilter]
