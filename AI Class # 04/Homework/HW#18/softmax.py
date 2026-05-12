import math

similarity_scores = [0.91, 0.74, 0.65, 0.11]

def softmax(scores):
    exp_values = [math.exp(s) for s in scores]
    total = sum(exp_values)
    weights = [v / total for v in exp_values]
    rounded = [round(w, 2) for w in weights]
    return rounded

attention_weights = softmax(similarity_scores)

print("Similarity scores:", similarity_scores)
print("Softmax attention weights:", attention_weights)
print("Sum of weights:", sum(attention_weights))