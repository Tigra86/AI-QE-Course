import math
import os
from scenarios import SCENARIOS

def softmax(logits):
    # Numerical stability: subtract max logit [cite: 22]
    max_logit = max(logits)
    exps = [math.exp(logit - max_logit) for logit in logits]
    sum_exps = sum(exps)
    return [exp / sum_exps for exp in exps]

def entropy(target, predicted, eps=1e-12):
    # Cross-entropy calculation [cite: 5]
    res = 0
    for t, p in zip(target, predicted):
        if t > 0:
            res += t * math.log(p + eps)
    return -res

def run_simulation():
    # Ensure output directory exists [cite: 25]
    if not os.path.exists('outputs'):
        os.makedirs('outputs')

    for scene in SCENARIOS:
        filename = f"outputs/{scene['id']}_{scene['name']}.txt"
        with open(filename, 'w') as f:
            f.write(f"OPTIMIZATION LOG: {scene['name']}\n")
            f.write("="*40 + "\n")
            
            logits = scene['logits']
            target = scene['target']
            labels = scene['labels']

            # Simulate 10 iterations of the Optimizer [cite: 7, 13]
            for step in range(11):
                probs = softmax(logits)
                current_loss = entropy(target, probs)
                
                # Format output for file
                prob_str = ", ".join([f"{l}: {p:.3f}" for l, p in zip(labels, probs)])
                f.write(f"Step {step:2d} | Loss: {current_loss:.4f} | Probs: [{prob_str}]\n")

                # Optimizer: Update Logits using Gradient nudge [cite: 18, 19]
                # If predicted prob is lower than target, push logit up
                for i in range(len(logits)):
                    if probs[i] < target[i]:
                        logits[i] += 0.1
                    else:
                        logits[i] -= 0.1
            
            f.write("\nFinal Prediction: " + labels[probs.index(max(probs))] + "\n")

if __name__ == "__main__":
    run_simulation()
    print("Simulation complete. Check the 'outputs/' folder for results.")