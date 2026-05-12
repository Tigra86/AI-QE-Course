import requests
import sys
import json

API_URL = "https://alex.academy/ai/score/api.php"

def call_api(action, name=None, value=None):

    params = {"action": action}

    if name is not None:
        params["name"] = name

    if value is not None:
        params["value"] = value

    response = requests.get(
        API_URL,
        params=params,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python query_tool.py <action>")
        print("  python query_tool.py student_search \"Name\"")
        print("  python query_tool.py completed_less_than 30")
        print("  python query_tool.py completed_under_percent 50")
        return

    action = sys.argv[1]

    if action in ["completed_less_than", "completed_under_percent"]:
        if len(sys.argv) < 3:
            print("This action requires a numeric value.")
            return
        value = sys.argv[2]
        result = call_api(action, value=value)

    elif action == "student_search":
        if len(sys.argv) < 3:
            print("student_search requires a name.")
            return
        name = sys.argv[2]
        result = call_api(action, name=name)

    # Handle simple actions (no parameters)
    else:
        result = call_api(action)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
