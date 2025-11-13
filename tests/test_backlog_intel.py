from ai.backlog_intel import score_task, prioritize


def test_score_and_prioritize():
    tasks = [
        {'id': 't1', 'severity': 'critical', 'effort': 1, 'impact': 9, 'age_days': 10},
        {'id': 't2', 'severity': 'minor', 'effort': 5, 'impact': 3, 'age_days': 1},
        {'id': 't3', 'severity': 'major', 'effort': 2, 'impact': 7, 'age_days': 3}
    ]
    scored = prioritize(tasks)
    assert scored[0]['id'] == 't1'
    assert scored[-1]['id'] == 't2'
