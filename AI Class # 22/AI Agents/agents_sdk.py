# pip install openai-agents simpleeval

from agents import Agent, Runner, function_tool
from simpleeval import simple_eval

# TOOL
@function_tool
def calculator(expression: str) -> str:
    return str(simple_eval(expression))

# AGENTS
math_tutor = Agent(
    name="Math Tutor",
    instructions=(
        "You are a concise math teaching assistant. "
        "Always use the calculator tool."
    ),
    tools=[calculator],
    model="gpt-5.2"
)

general_tutor = Agent(
    name="General Tutor",
    instructions=(
        "You are a concise teaching assistant.\n"
        "- If math → handoff to Math Tutor\n"
        "- Otherwise answer normally"
    ),
    handoffs=[math_tutor],
    model="gpt-5.2"
)

# RUN
questions = [
    "Explain what an AI agent is in one paragraph.",
    "What is 18 * 7 + 4?",
]

for q in questions:
    result = Runner.run_sync(general_tutor, q)

    print("\n" + "=" * 50)
    print(f"User: {q}")
    print("Final agent:", result.last_agent.name)
    print("Answer:", result.final_output)
