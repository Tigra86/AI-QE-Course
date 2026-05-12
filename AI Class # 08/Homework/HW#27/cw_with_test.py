from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime
import re
import json
import tiktoken
import textwrap

# ===========================
# CONFIG
# ===========================
MAX_CONTEXT_TOKENS = 100
OVERHEAD = 4
WARN_AT = 0.8
OVERFLOW_LOG = "overflow_events.jsonl"

# ===========================
# Tokenizer
# ===========================
ENCODING = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(ENCODING.encode(text))

# ===========================
# Message model
# ===========================
@dataclass
class Message:
    role: str   # system | user
    content: str

# ===========================
# Normalization
# ===========================
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ===========================
# Memory extraction
# ===========================
def extract_memory(users: List[Message]) -> Optional[Message]:
    memory = {}
    timestamps = {}

    for m in users:
        norm = normalize(m.content)
        now = datetime.utcnow().isoformat(timespec="seconds")

        m_name = re.search(r"\bmy n[a-z]{1,2}e (is )?(?P<name>[a-z]+)\b", norm)
        if m_name:
            memory["name"] = m_name.group("name").capitalize()
            timestamps["name"] = now

        m_age = re.search(r"\bi am (?P<age>\d{1,3}) years? old\b", norm)
        if m_age:
            age = int(m_age.group("age"))
            if 0 < age < 130:
                memory["age"] = str(age)
                timestamps["age"] = now

        m_loc = re.search(r"\bi live in (?P<loc>[a-z ]+)\b", norm)
        if m_loc:
            memory["location"] = m_loc.group("loc").title()
            timestamps["location"] = now

        m_hobby = re.search(r"\bi like (?P<hobby>[a-z ]+)\b", norm)
        if m_hobby:
            hobby = m_hobby.group("hobby").strip()
            if len(hobby.split()) <= 4:
                memory["hobby"] = hobby
                timestamps["hobby"] = now

    if not memory:
        return None

    lines = ["MEMORY SUMMARY:"]
    for k in ("name", "age", "location", "hobby"):
        if k in memory:
            lines.append(f"- {k.capitalize()}: {memory[k]} (updated {timestamps[k]})")

    return Message(role="system", content="\n".join(lines))

# ===========================
# Build Pre-Trim Prompt
# ===========================
def build_pretrim_prompt(system_msg: Message, users: List[Message], memory: Optional[Message]) -> List[Message]:
    prompt = [system_msg]
    if memory:
        prompt.append(memory)
    prompt.extend(users)
    return prompt

# ===========================
# Enforce context limit
# ===========================
def enforce_context_limit(
    messages: List[Message],
    max_tokens: int,
    overhead: int
) -> Tuple[List[Message], List[Message]]:

    system_msgs = [m for m in messages if m.role == "system"]
    user_msgs = [m for m in messages if m.role == "user"]

    last_user = user_msgs[-1] if user_msgs else None
    older_users = user_msgs[:-1]

    kept = []
    total = 0

    # Pin SYSTEM + MEMORY
    for m in system_msgs:
        cost = count_tokens(m.content) + overhead
        kept.append(m)
        total += cost

    # Pin LAST USER QUESTION
    if last_user:
        cost = count_tokens(last_user.content) + overhead
        if total + cost <= max_tokens:
            kept.append(last_user)
            total += cost

    # Add older USER messages (newest first)
    kept_older = []
    for m in reversed(older_users):
        cost = count_tokens(m.content) + overhead
        if total + cost > max_tokens:
            break
        kept_older.insert(0, m)
        total += cost

    # Reassemble: [System/Memory] + [Old Kept] + [Last User]
    split_idx = len(system_msgs)
    final_list = kept[:split_idx] + kept_older
    if last_user in kept:
        final_list.append(last_user)
        
    dropped = [m for m in messages if m not in final_list]
    return final_list, dropped

# ===========================
# Answer strictly from memory
# ===========================
def answer_from_memory(context_text: str) -> str:
    name = age = location = hobby = None

    for line in context_text.splitlines():
        if line.startswith("- Name:"):
            name = line.split(":", 1)[1].split("(")[0].strip()
        if line.startswith("- Age:"):
            age = line.split(":", 1)[1].split("(")[0].strip()
        if line.startswith("- Location:"):
            location = line.split(":", 1)[1].split("(")[0].strip()
        if line.startswith("- Hobby:"):
            hobby = line.split(":", 1)[1].split("(")[0].strip()

    text = context_text.lower()
    if "what is my name" in text:
        return f"Your name is {name}." if name else "I don't know your name."
    if "how old am i" in text:
        return f"You are {age} years old." if age else "I don't know your age."
    if "where do i live" in text:
        return f"You live in {location}." if location else "I don't know where you live."
    if "what do i like" in text:
        return f"You like {hobby}." if hobby else "I don't know what you like."

    return "I can only answer questions about saved memory."

# ===========================
# Rendering helpers
# ===========================
def token_total(messages: List[Message]) -> int:
    return sum(count_tokens(m.content) + OVERHEAD for m in messages)

def render_bar(label: str, used: int, max_tokens: int, width: int = 40) -> str:
    ratio = min(used / max_tokens, 1.0)
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    status = "FULL" if used >= max_tokens else f"{int(ratio * 100)}%"
    return f"{label}\n[{bar}] {used} / {max_tokens} tokens ({status})"

def render_evicted_bar(evicted: int, max_tokens: int, width: int = 40) -> str:
    ratio = min(evicted / max_tokens, 1.0)
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    return f"EVICTED TOKENS (WHAT WAS REMOVED)\n[{bar}] {evicted} tokens removed"

def render_context(messages: List[Message]) -> str:
    return "\n\n".join(f"{m.role.upper()}: {m.content}" for m in messages)

def print_box(title: str, text: str):
    print("=" * 90)
    print(title)
    print("-" * 90)
    for line in text.split("\n"):
        print("\n".join(textwrap.wrap(line, 90)))
    print("=" * 90)

# ===========================
# Overflow logging
# ===========================
def log_overflow(pre, post, dropped):
    event = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
        "pre_tokens": token_total(pre),
        "post_tokens": token_total(post),
        "evicted_tokens": token_total(pre) - token_total(post),
        "evicted_messages": [
            {"role": m.role, "content": m.content} for m in dropped
        ]
    }
    with open(OVERFLOW_LOG, "a") as f:
        f.write(json.dumps(event) + "\n")

# ===========================
# Test Suite
# ===========================
def run_eviction_test():
    system_msg = Message("system", "You are a helpful assistant.")
    memory = Message("system", "MEMORY SUMMARY:\n- Name: John\n- Age: 39\n- Location: SF")
    
    users = [
        Message("user", "Old message A: " + "word " * 10), 
        Message("user", "Old message B: " + "word " * 10),
        Message("user", "This is the current question?") 
    ]
    
    pre = build_pretrim_prompt(system_msg, users, memory)
    post, dropped = enforce_context_limit(pre, MAX_CONTEXT_TOKENS, OVERHEAD)
    
    print_box("TEST: EVICTION CHECK", 
              f"Pre-trim: {token_total(pre)} tokens\n"
              f"Post-trim: {token_total(post)} tokens\n"
              f"Dropped count: {len(dropped)}")
    
    if dropped:
        for m in dropped:
            print(f"SUCCESSFULLY EVICTED: {m.content[:50]}...")

# ===========================
# Main Entry Point
# ===========================
def main():
    system_msg = Message("system", "You are a helpful assistant.")
    users: List[Message] = []

    print("\n[BOOTING] Context Window Engine starting...")
    print(f"[INFO] Using Tokenizer: {ENCODING.name}")
    
    print_box(
        "FINAL CONTEXT WINDOW ENGINE",
        "Commands: /test | /reset | /quit\nStatus: System Ready"
    )

    while True:
        try:
            user_input = input("\nREADY --- Type message or command: \nUSER > ").strip()
        except EOFError:
            print("\n[EXIT] Session ended.")
            break

        if not user_input:
            continue
            
        if user_input.lower() == "/quit":
            print("[EXIT] Shutting down...")
            break
            
        if user_input.lower() == "/reset":
            users = []
            print("\n[SYSTEM] Conversation history cleared.")
            continue
            
        if user_input.lower() == "/test":
            run_eviction_test()
            continue

        users.append(Message(role="user", content=user_input))
        memory = extract_memory(users)
        pre = build_pretrim_prompt(system_msg, users, memory)
        post, dropped = enforce_context_limit(pre, MAX_CONTEXT_TOKENS, OVERHEAD)
        
        if dropped:
            log_overflow(pre, post, dropped)
            print(render_evicted_bar(token_total(dropped), MAX_CONTEXT_TOKENS))

        print(render_bar("CURRENT CONTEXT LOAD", token_total(post), MAX_CONTEXT_TOKENS))
        
        if "?" in user_input:
            context_text = render_context(post)
            print(f"\nASSISTANT > {answer_from_memory(context_text)}")

# Explicit ignition switch
if __name__ == "__main__":
    main()