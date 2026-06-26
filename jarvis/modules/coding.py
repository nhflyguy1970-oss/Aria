import subprocess
from pathlib import Path

from jarvis import fs, llm
from jarvis.config import PROJECT_ROOT
from jarvis.conversation import Conversation
from jarvis.diff_util import show_diff


class CodingEngine:
    def __init__(self):
        self.conversation = Conversation(
            "You are Jarvis Coding Engine, a helpful programming assistant."
        )
        self.project_root: Path | None = None
        self.project_files: list[str] = []
        self.loaded_files: list[dict] = []
        self.search_root = PROJECT_ROOT

    def _base(self) -> Path:
        return self.project_root or self.search_root

    def load_file(self, path: str) -> str:
        content = fs.read_file(path, base=self._base())
        if content.startswith("ERROR:"):
            return content
        self.loaded_files.append({"path": path, "content": content})
        self.conversation.add_system(f"Loaded file: {path}\n\n{content}")
        return "OK"

    def review_project(self) -> None:
        if not self.project_root:
            print("\nNo project loaded. Use: project <folder>\n")
            return

        important_files = []
        for path in self.project_files:
            lower = path.lower()
            if (
                ".history" not in lower
                and ".log" not in lower
                and "__pycache__" not in lower
                and (
                    "readme" in lower
                    or lower.endswith(("main.py", "app.py", "server.py", "index.py", "config.py"))
                )
            ):
                important_files.append(path)

        if not important_files:
            for path in self.project_files:
                lower = path.lower()
                if lower.endswith((".py", ".sh", ".yml", ".yaml", ".json")):
                    important_files.append(path)
            important_files = important_files[:25]

        context = ""
        max_context = 12000
        for path in important_files[:20]:
            full_path = self.project_root / path
            content = fs.read_file(str(full_path), base=self.project_root)
            if content.startswith("ERROR:"):
                continue
            chunk = f"\n\nFILE: {path}\n\n{content[:1000]}"
            if len(context) + len(chunk) > max_context:
                break
            context += chunk

        print(f"\nReviewing {len(important_files)} files...")
        print("\nFiles selected:\n")
        for path in important_files[:5]:
            print(path)
        print(f"\nContext size: {len(context)} characters\n")
        print(f"Indexed Files: {len(self.project_files)}")
        print(f"Review Files: {len(important_files)}\n")

        prompt = f"""You are a senior software architect. Review this project.
Do NOT generate code.

PROJECT PURPOSE
ARCHITECTURE
HIGH PRIORITY ISSUES
MEDIUM PRIORITY ISSUES
LOW PRIORITY ISSUES
BUG RISKS
REFACTORING OPPORTUNITIES
UPGRADE RECOMMENDATIONS

Do NOT summarize files. Focus on improvements and risks.

PROJECT ROOT: {self.project_root}

PROJECT:
{context}
"""
        answer = llm.ask(llm.review_model(), [{"role": "user", "content": prompt}])
        print()
        print(answer)
        print()

    def fix_file(self, path: str) -> None:
        content = fs.read_file(path, base=self._base())
        if content.startswith("ERROR:"):
            print(f"\n{content}\n")
            return

        try:
            result = subprocess.run(
                ["python3", str(fs.resolve_path(path, base=self._base()))],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception as e:
            print(f"\nERROR: {e}\n")
            return

        if not result.stderr:
            print("\nNo errors detected.\n")
            return

        prompt = f"""The following Python file has errors. Fix the file.

Format your response exactly like this:

EXPLANATION:
- fix 1

CODE:
<complete corrected file>

Do not use markdown. Do not use code fences.

ERRORS:
{result.stderr}

FILE:
{content}
"""
        response_text = llm.ask(llm.coder_model(), [{"role": "user", "content": prompt}])
        explanation, fixed_code = llm.parse_code_response(response_text)

        print("\nSuggested fixes:\n")
        print(explanation)
        print()
        show_diff(content, fixed_code)

        if input("View full proposed file? (y/n): ").lower() == "y":
            print("\n--- PROPOSED FILE ---\n")
            print(fixed_code)
            print()

        if input("Write fix? (y/n): ").lower() != "y":
            print("\nCancelled.\n")
            return

        backup = fs.backup_file(path, base=self._base())
        print(f"\nBackup created:\n{backup}")
        fs.write_file(path, fixed_code, base=self._base())
        print("\nFile updated.\n")

    def improve_file(self, path: str) -> None:
        content = fs.read_file(path, base=self._base())
        if content.startswith("ERROR:"):
            print(f"\n{content}\n")
            return

        prompt = f"""Improve the following code.

Format:

EXPLANATION:
- improvement 1

CODE:
<complete improved file>

Do not use markdown. Do not use code fences.

FILE:
{content}
"""
        response_text = llm.ask(llm.coder_model(), [{"role": "user", "content": prompt}])
        explanation, improved_code = llm.parse_code_response(response_text)

        print("\nSuggested improvements:\n")
        print(explanation)
        print()
        show_diff(content, improved_code)

        if input("View full proposed file? (y/n): ").lower() == "y":
            print("\n--- PROPOSED FILE ---\n")
            print(improved_code)
            print()

        if input("Write changes? (y/n): ").lower() != "y":
            print("\nCancelled.\n")
            return

        backup = fs.backup_file(path, base=self._base())
        print(f"\nBackup created:\n{backup}")
        fs.write_file(path, improved_code, base=self._base())
        print("\nFile updated.\n")

    def run_file(self, path: str) -> None:
        try:
            resolved = fs.resolve_path(path, base=self._base())
            result = subprocess.run(
                ["python3", str(resolved)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            print("\n--- OUTPUT ---\n")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("\n--- ERRORS ---\n")
                print(result.stderr)
            print()
        except Exception as e:
            print(f"\nERROR: {e}\n")

    def handle(self, prompt: str) -> bool:
        """Handle one prompt. Returns False to exit."""
        if prompt.lower() == "exit":
            return False

        if prompt.startswith("read "):
            path = prompt[5:].strip()
            content = fs.read_file(path, base=self._base())
            if content.startswith("ERROR:"):
                print(f"\n{content}\n")
            else:
                print(f"\nLoaded: {path}\n")
                self.conversation.add_system(f"Loaded file: {path}\n\n{content}")
            return True

        if prompt.startswith("improve "):
            self.improve_file(prompt[8:].strip())
            return True

        if prompt.startswith("fix "):
            self.fix_file(prompt[4:].strip())
            return True

        if prompt.startswith("run "):
            self.run_file(prompt[4:].strip())
            return True

        if prompt.startswith("replace "):
            path = prompt[8:].strip()
            print("\nOld text:")
            old_text = input()
            print("\nNew text:")
            new_text = input()
            result = fs.replace_text(path, old_text, new_text, base=self._base())
            if result == "TEXT NOT FOUND":
                print("\nText not found.\n")
            elif result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print("\nBackup created:")
                print(result)
                print("\nReplacement complete.\n")
            return True

        if prompt.startswith("find "):
            matches = fs.find_files(prompt[5:].strip(), self._base())
            if matches:
                print("\nFound:\n")
                for match in matches:
                    print(match)
                print()
            else:
                print("\nNo matches found.\n")
            return True

        if prompt.startswith("search "):
            results = fs.search_files(prompt[7:].strip(), self._base())
            if results:
                print("\nFound:\n")
                for path, line_num, line in results[:50]:
                    print(f"{path}:{line_num}: {line}")
                print()
            else:
                print("\nNo matches found.\n")
            return True

        if prompt.startswith("show "):
            print()
            fs.show_file(prompt[5:].strip(), base=self._base())
            print()
            return True

        if prompt.startswith("project "):
            target = prompt[8:].strip()
            if target.startswith("search "):
                if not self.project_root:
                    print("\nNo project loaded.\n")
                    return True
                results = fs.search_files(target[7:].strip(), self.project_root)
                if results:
                    print("\nFound:\n")
                    for path, line_num, line in results[:50]:
                        print(f"{path}:{line_num}: {line}")
                    print()
                else:
                    print("\nNo matches found.\n")
                return True

            if target == "files":
                if not self.project_files:
                    print("\nNo project loaded.\n")
                else:
                    print("\nProject Files:\n")
                    for path in self.project_files:
                        print(path)
                    print()
                return True

            self.project_root, self.project_files = fs.scan_project(target)
            self.search_root = self.project_root
            print(f"\nProject loaded.\n\n{len(self.project_files)} files indexed.\n")
            return True

        if prompt.startswith("load "):
            result = self.load_file(prompt[5:].strip())
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nLoaded: {prompt[5:].strip()}")
                print(f"\n{len(self.loaded_files)} file(s) loaded.\n")
            return True

        if prompt == "review project":
            self.review_project()
            return True

        if prompt == "clear":
            self.conversation.clear()
            print("\nConversation cleared.\n")
            return True

        # Free-form chat — only path that hits the LLM
        self.conversation.add_user(prompt)
        answer = llm.ask(llm.coder_model(), self.conversation.messages)
        self.conversation.add_assistant(answer)
        print()
        print(answer)
        print()
        return True


def main():
    engine = CodingEngine()
    print("\nJarvis Coding Engine")
    print("Type 'exit' to quit.")
    print("Commands:")
    print("  read <path>       load file into context")
    print("  load <file>       load file (tracked)")
    print("  improve <path>    suggest code improvements")
    print("  fix <path>        fix Python errors")
    print("  find <name>       search filenames")
    print("  search <text>     search file contents")
    print("  show <path>       display file with line numbers")
    print("  replace <path>    interactive find-and-replace")
    print("  run <path>        execute Python file")
    print("  project <folder>  index a project")
    print("  project files     list indexed files")
    print("  project search <text>")
    print("  review project    architecture review")
    print("  clear             reset conversation\n")

    while True:
        try:
            prompt = input("Coding > ")
            if not engine.handle(prompt):
                break
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"\nERROR: {e}\n")
