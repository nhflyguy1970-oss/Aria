from jarvis import llm
from jarvis.branding import assistant_intro
from jarvis.conversation import Conversation
from jarvis.modules.memory import MemoryStore

class GeneralEngine:
    """CLI-only general chat engine (GUI uses JarvisAssistant directly)."""

    def __init__(self, memory: MemoryStore | None = None):
        self.conversation = Conversation(
            f"You are {assistant_intro()}, your friendly AI buddy. "
            "Be concise, accurate, and friendly."
        )
        self.mem = memory or MemoryStore()

    def handle(self, prompt: str) -> bool:
        if prompt.lower() == "exit":
            return False

        if prompt == "clear":
            self.conversation.clear()
            print("\nConversation cleared.\n")
            return True

        if prompt.startswith("remember "):
            text = prompt[9:].strip()
            self.mem.add("fact", text)
            print(f"\nRemembered: {text}\n")
            return True

        if prompt == "recall":
            facts = self.mem.list_entries("fact")
            if facts:
                print("\nRecalled facts:\n")
                for entry in facts[-10:]:
                    print(f"  - {entry['content']}")
                print()
            else:
                print("\nNo facts stored.\n")
            return True

        if prompt.startswith("search memory "):
            query = prompt[14:].strip()
            results = self.mem.search(query)
            if results:
                print("\nMemory matches:\n")
                for entry in results:
                    print(f"  [{entry['type']}] {entry['content']}")
                print()
            else:
                print("\nNo matches.\n")
            return True

        memories = self.mem.search(prompt, limit=3)
        user_content = prompt
        if memories:
            context = "Relevant memories:\n" + "\n".join(
                f"- {m['content']}" for m in memories
            )
            user_content = f"{context}\n\nUser: {prompt}"

        self.conversation.add_user(user_content)
        answer = llm.ask(llm.general_model(), self.conversation.messages)
        self.conversation.add_assistant(answer)
        print()
        print(answer)
        print()
        return True

def main():
    engine = GeneralEngine()
    print("\nJarvis General Assistant")
    print("Type 'exit' to quit.")
    print("Commands:")
    print("  remember <text>      store a fact")
    print("  recall               show stored facts")
    print("  search memory <text> search memory")
    print("  clear                reset conversation")
    print("  (anything else)      chat\n")

    while True:
        try:
            prompt = input("General > ")
            if not engine.handle(prompt):
                break
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"\nERROR: {e}\n")
