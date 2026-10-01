import os
from pathlib import Path

import ollama
from ollama import ResponseError

from memory import Vault, make_tools
from datetime import date

from colorama import Fore, Style, init
init(autoreset=True) # This makes sure colors reset automatically!

MODEL = os.environ.get("CYDONIA_MODEL", "gemma4:e4b")  # any tool-capable Ollama model
BASE = Path(__file__).parent
MAX_TOOL_ROUNDS = 6

vault = Vault(BASE / "vault")
tools = make_tools(vault)
tool_map = {t.__name__: t for t in tools}


def build_system_prompt() -> str:
    system = (BASE / "brain" / "system.md").read_text(encoding="utf-8")

    index = vault.read("MEMORY.md")
    files = "\n".join(f"- {f}" for f in vault.list_files())

    identity_path = BASE / "brain" / "identity.md"
    identity = identity_path.read_text(encoding="utf-8") if identity_path.exists() else ""
    
    return (f"{system}\n\n{identity}\n\nToday's date: {date.today().isoformat()}"
            f"\n\n# MEMORY INDEX\n{index}\n\n# FILES IN VAULT\n{files}")

def chat_safe(messages):
    # retry at lower temperature if the model emits malformed output
    for temp in (0.7, 0.4, 0.1):
        try:
            return ollama.chat(model=MODEL, messages=messages, tools=tools,
                               options={"temperature": temp})
        except ResponseError as e:
            if e.status_code != 500:
                raise
            print(f"  [bad model output, retrying at temp {temp}]")
    return None

def run_turn(messages: list) -> str:
    for _ in range(MAX_TOOL_ROUNDS):
        resp = chat_safe(messages)
        if resp is None:
            return "(the model kept producing broken output; try rephrasing)"
        msg = resp.message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content
        for call in msg.tool_calls:
            fn = tool_map.get(call.function.name)
            try:
                result = fn(**call.function.arguments) if fn else "unknown tool"
            except Exception as e:  # keep the loop alive if the model sends bad args
                result = f"error: {e}"
            print(f"  [{call.function.name}] {str(call.function.arguments)[:80]}")
            messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})
    return "(stopped: too many tool rounds)"


def main():
    messages = [{"role": "system", "content": build_system_prompt()}]
    print(f"Cydonia online ({MODEL}). Ctrl+C or 'exit' to quit.\n")
    print("Initializing...\n")

    messages.append({
        "role": "user",
        "content": (
            "[SYSTEM EVENT: STARTUP]\n"
            "Cydonia has just been started. Wake up, initialize your "
            "current context and memory, and greet the user naturally."
        )
    })

    print("\ncydonia >", run_turn(messages), "\n")

    while True:
        try:
            user = input(Fore.LIGHTRED_EX + "you > ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if user.lower() in {"exit", "quit"}:
            break
        if not user:
            continue
        messages.append({"role": "user", "content": user})
        print("\ncydonia >", run_turn(messages), "\n")


if __name__ == "__main__":
    main()
