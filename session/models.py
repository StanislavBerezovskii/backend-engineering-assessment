from django.db import models

from quiz.models import Answer, Question, Quiz
from users.models import User


class QuizSession(models.Model):
    """Quiz session model - a user attempt to take the quiz"""
    user = models.ForeignKey(User,
                             related_name='session',
                             on_delete=models.SET_NULL,
                             null=True)
    quiz = models.ForeignKey(Quiz,
                             related_name='session',
                             on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0)
    is_completed = models.BooleanField(default=False)

    def calculate_score(self):
        """Calculates and saves the user score for this session"""
        correct_responses = 0
        total_questions = self.quiz.question_count
        responses = self.responses.select_related('question', 'selected_answer')

        for response in responses:
            if response.selected_answer.is_correct:
                correct_responses += 1

        self.score = (correct_responses / total_questions) * 100
        self.is_completed = True
        self.completed_at = models.DateTimeField(auto_now_add=True)
        self.save()

    def __str__(self):
        return f'Session: {self.user.username} - {self.quiz.title} - {"Completed" if self.is_completed else "In Progress"}'


class Response(models.Model):
    """Quiz session user response model"""
    session = models.ForeignKey(QuizSession,
                                related_name='responses',
                                on_delete=models.CASCADE)
    question = models.ForeignKey(Question,
                                 on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer,
                                        on_delete=models.CASCADE)

    def __str__(self):
        return f'Response: session {self.session.id} - {self.question.prompt} - {self.selected_answer.answer_text}'
