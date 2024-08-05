


@csrf_exempt
def session(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = list(Question.objects.filter(quiz=quiz))

    if 'question_index' not in request.session:
        request.session['question_index'] = 0
        request.session['answers'] = {}

    if request.method == 'POST':
        question_index = request.session['question_index']
        selected_answer = request.POST.get('answer')

        if selected_answer:
            request.session['answers'][questions[question_index].id] = int(selected_answer)
            request.session.modified = True

        question_index += 1
        if question_index >= len(questions):
            return redirect('results', quiz_id=quiz_id)

        request.session['question_index'] = question_index
        return redirect(reverse('session', args=[quiz_id]))

    question_index = request.session['question_index']

    if question_index >= len(questions):
        return redirect('results', quiz_id=quiz_id)

    question = questions[question_index]
    answers = Answer.objects.filter(question=question)

    return render(request, 'session.html', {
        'quiz': quiz,
        'question': question,
        'answers': answers,
        'question_index': question_index + 1,
        'total_questions': len(questions),
    })


@csrf_exempt
def results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz)
    answers = Answer.objects.all()

    correct_answers = 0

    for question in questions:
        selected_answer_id = request.session['answers'].get(question.id)
        if selected_answer_id:
            selected_answer = get_object_or_404(Answer, id=selected_answer_id)
            if selected_answer.is_correct:
                correct_answers += 1

    request.session.pop('question_index', None)
    request.session.pop('answers', None)

    return render(request, 'results.html', {
        'quiz': quiz,
        'correct_answers': correct_answers,
        'total_questions': questions.count(),
    })