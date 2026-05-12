from openai import OpenAI

client = OpenAI()

def test_explainability_std_dev():

    response = client.responses.create(
        model="gpt-5.2",
        input="Explain how you calculated the standard deviation."
    )

    text = response.output_text.lower()

    print("--------------------------------------------------")
    print(response.output_text)
    print("--------------------------------------------------")

    # Core statistical concepts must be mentioned
    assert "mean" in text, "Missing explanation of mean"
    assert "variance" in text, "Missing explanation of variance"

    # Optional but stronger explainability checks
    assert "square" in text or "squared" in text, "Missing squaring step"
    assert "difference" in text or "deviation" in text, "Missing deviation step"
    assert "divide" in text or "average" in text, "Missing averaging step"
    assert "square root" in text, "Missing square root step"

    print("Explainability OK.")

if __name__ == "__main__":
    test_explainability_std_dev()