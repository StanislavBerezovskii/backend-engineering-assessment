from django.db import models

from users.models import User


class Quiz(models.Model):
    """Quiz model"""
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=None)
    title = models.CharField(max_length=255, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    times_taken = models.IntegerField(default=0, editable=False)

    @property
    def question_count(self):
        """Returns the number of questions in the quiz"""
        return self.questions.count()

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ['id']

    def __str__(self):
        return self.title


class Question(models.Model):
    """"Question model"""
    quiz = models.ForeignKey(Quiz,
                             related_name='questions',
                             on_delete=models.DO_NOTHING)
    prompt = models.CharField(max_length=255,
                              default='')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.prompt


class Answer(models.Model):
    """Answer model"""
    question = models.ForeignKey(Question,
                                 related_name='answers',
                                 on_delete=models.DO_NOTHING)
    answer_text = models.CharField(max_length=255,
                                   default='')
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.answer_text
