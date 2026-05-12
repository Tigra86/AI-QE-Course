SCENARIOS = [
    {
        "id": 1,
        "name": "Spam_Filter",
        "labels": ["SPAM", "NOT_SPAM"],
        "target": [1.0, 0.0],
        "logits": [0.1, 0.9]
    },
    {
        "id": 2,
        "name": "Medical_Diagnosis",
        "labels": ["FLU", "COVID", "COLD"],
        "target": [0.7, 0.2, 0.1],
        "logits": [0.33, 0.33, 0.33]
    },
    {
        "id": 3,
        "name": "Sentiment_Analysis",
        "labels": ["POSITIVE", "NEUTRAL", "NEGATIVE"],
        "target": [0.2, 0.6, 0.2],
        "logits": [0.8, 0.1, 0.1]
    },
    {
        "id": 4,
        "name": "Translation_Hallucination",
        "labels": ["MAT", "FLOOR", "PIZZA"],
        "target": [0.5, 0.5, 0.0],
        "logits": [0.0, 0.0, 0.9]
    },
    {
        "id": 5,
        "name": "Driving_Object_Detection",
        "labels": ["STOP_SIGN", "YIELD", "SPEED_LIMIT"],
        "target": [1.0, 0.0, 0.0],
        "logits": [0.4, 0.5, 0.1]
    }
]