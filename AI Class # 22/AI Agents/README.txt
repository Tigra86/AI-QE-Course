# AI Agents Lab Notes & Execution History

A sequential log and architectural breakdown of the AI Agent scripts executed on a macOS Mac mini workstation (Bash environment) using Python.

---

## 🧭 Step-by-Step Execution History

This is the exact sequence followed to configure the environment, test stateless baselines, implement memory, resolve syntax warnings, and run multi-step tool loops.

### Step 1: Baseline Tool-Use Execution
* **Command:** `python agent_multiply.py`
* **Result:** Successful. The agent parsed a math question, triggered a single-step local function calling block, computed the math using Python, and returned the correct calculation to the user.

### Step 2: Session Memory Verification
* **Command:** `python agent_memory.py`
* **Result:** Successful. Tested multi-turn conversation tracking. The model retained names and locations across separate dialogue exchanges, demonstrating stateful array management.

### Step 3: Package Installation & Multi-Agent Orchestration
* **Commands:**
  ```bash
  pip install openai-agents
  python agents_sdk.py
  ```
* **Encountered Error:** `ModuleNotFoundError: No module named 'simpleeval'`
* **Resolution:** Installed the missing dependency via `pip install simpleeval` and re-ran the script.
* **Result:** Successfully demonstrated intent-based routing. The script routed a general description question to a basic tutor node, then dynamically performed a session handoff to a math tutor node for an algebraic question.
* **Code Modification Note:** Handled framework syntax warnings regarding spaces in agent names by replacing `"Math Tutor"` and `"General Tutor"` with valid alphanumeric/underscore variable names (`"Math_Tutor"`, `"General_Tutor"`).

### Step 4: Authentication & Stateless Framework Check
* **Command:** `python anthropic_basic.py`
* **Encountered Error:** `TypeError: "Could not resolve authentication method..."`
* **Resolution:** Verified the environment variables inside `~/.bashrc`. Ensured the `export` keyword preceded the variable (`export ANTHROPIC_API_KEY="..."`) and executed `source ~/.bashrc` to update the active Bash process memory.
* **Result:** The script executed successfully but highlighted baseline limitations—without tools or memory hooks, the raw model natively refused to provide real-time Paris weather information.

### Step 5: Advanced ReAct Tool Loop Execution
* **Command:** `python anthropic_basic_agent.py`
* **Result:** Successful. Demonstrated a continuous autonomous reasoning loop (`while True:`). The agent intercepted a complex, multi-variable question, sequentially triggered live external geocoding/weather requests via `requests`, executed a local trigonometric distance formula, and delivered an integrated report.

---

## 🏛️ Summary of AI Agent Architectures

### 1. Stateful Chat Memory Loop (`agent_memory.py`)
* **Core Concept:** Standard LLM API endpoints are completely stateless. Context tracking requires building an external runtime state layer.
* **Mechanism:** Maintains an active conversation array (`self.messages`). Every user input and generated assistant output is continuously appended and resent to the model, giving the agent a working memory.

### 2. Single-Step Function Calling (`agent_multiply.py`)
* **Core Concept:** Decouples text generation from structured processing to bypass mathematical hallucination.
* **Mechanism:** Equips the model with strict JSON schema definitions of local functions. The model outputs a structural tool call payload instead of raw text, letting the underlying Python system run exact computations locally before drafting a final response.

### 3. Intent Routing & Multi-Agent Frameworks (`agents_sdk.py`)
* **Core Concept:** Instead of scaling a single agent into a monolithic, unmanageable script, tasks are partitioned into isolated, modular micro-agents.
* **Mechanism:** Utilizes an orchestration framework (`openai-agents`). A supervisor node evaluates incoming text intents and dynamically issues a secure handoff function call, transferring session control to specialized domain-specific nodes.

### 4. Continuous Multi-Step ReAct Loops (`anthropic_basic_agent.py`)
* **Core Concept:** Complex, unstructured problems require an automated loop capable of chaining observations, tool selections, and evaluations until a goal is achieved.
* **Mechanism:** Runs a loop that continuously evaluates model responses. If the model determines it requires multiple external items (such as live weather parameters and coordinate distances), it executes multiple local tools sequentially, updates its internal context, and loops until text finalization is achieved.
