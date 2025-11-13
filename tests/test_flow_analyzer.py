from ai.analytics.flow_analyzer import aggregate_sum, detect_anomalies


def test_aggregator_and_anomaly():
    items = [{'value': 1}, {'value': 5}, {'value': 200}]
    s = aggregate_sum(items)
    assert s == 206
    a = detect_anomalies(items, threshold=100)
    assert len(a) == 1 and a[0]['value'] == 200
