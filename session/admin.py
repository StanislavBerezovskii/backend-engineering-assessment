from django.contrib import admin

from session.models import QuizSession, Response


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    """Handles the QuizSession model in the admin panel"""
    list_display = ['user', 'quiz', 'started_at', 'completed_at', 'score', 'is_completed',]
    list_filter = ['user', 'quiz', 'is_completed',]
    search_fields = ['user__username', 'quiz__title',]

    def has_add_permission(self, request):
        """Disallows adding quiz session from the admin panel"""
        return False


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    """Handles the Response model in the admin panel"""
    list_display = ['session', 'question', 'selected_answer',]
    list_filter = ['session__quiz',]
    search_fields = ['session__user__username', 'question__prompt', 'selected_answer__answer_text',]

    def has_add_permission(self, request):
        """Disallows adding session responses from the admin panel"""
        return False
