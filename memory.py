"""Memory Vault v0.1: plain Markdown files plus keyword search.

The LLM never holds the whole vault. It gets an index, then calls the
tools below to pull in only the notes it needs.
"""
from pathlib import Path
import re
import time

def _clean(text: str) -> str:
    # small models often send a literal backslash-n instead of a newline
    return text.replace("\\n", "\n").strip()


class Vault:
    def __init__(self, root: str = "vault"):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    # ---- safety: never let the model touch files outside the vault ----
    def _safe(self, rel: str) -> Path:
        p = (self.root / rel).resolve()
        if self.root not in p.parents and p != self.root:
            raise ValueError("Path escapes the vault")
        if p.suffix != ".md":
            raise ValueError("Only .md files are allowed")
        return p

    def list_files(self) -> list[str]:
        return sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*.md"))

    def read(self, rel: str) -> str:
        p = self._safe(rel)
        return p.read_text(encoding="utf-8") if p.exists() else f"(no such note: {rel})"

    def write(self, rel: str, content: str) -> str:
        p = self._safe(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():  # back up the old version before overwriting
            bak = self.root / ".history" / (rel.replace("/", "__") + f".{int(time.time())}.bak")
            bak.parent.mkdir(exist_ok=True)
            bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        content = _clean(content)
        p.write_text(content + "\n", encoding="utf-8")
        return f"wrote {rel} ({len(content)} chars)"

    def append(self, rel: str, text: str) -> str:
        p = self._safe(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        text = _clean(text)
        if p.exists() and text in p.read_text(encoding="utf-8"):
            return "already in note, nothing added"
        with p.open("a", encoding="utf-8") as f:
            f.write(("\n" if p.exists() and p.stat().st_size else "") + text + "\n")
        return f"appended to {rel}"

    def replace(self, rel: str, old: str, new: str) -> str:
        p = self._safe(rel)
        if not p.exists():
            return f"(no such note: {rel})"
        text = p.read_text(encoding="utf-8")
        old, new = _clean(old), _clean(new)
        if text.count(old) != 1:
            return f"error: old text must appear exactly once (found {text.count(old)})"
        return self.write(rel, text.replace(old, new))

    def search(self, query: str, limit: int = 5) -> list[dict]:
        words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2]
        hits = []
        for rel in self.list_files():
            text = self.read(rel)
            low = text.lower()
            score = sum(low.count(w) for w in words) + 3 * sum(w in rel.lower() for w in words)
            if score:
                line = next((l for l in text.splitlines() if any(w in l.lower() for w in words)), "")
                hits.append({"path": rel, "score": score, "snippet": line.strip()[:160]})
        return sorted(hits, key=lambda h: -h["score"])[:limit]


def make_tools(vault: Vault):
    """Return plain functions; Ollama builds the tool schemas from the docstrings."""

    def memory_search(query: str) -> str:
        """Search the memory vault by keywords. Use this first when you need
        something about the user, their projects, or past decisions.

        Args:
            query: Keywords to look for.
        """
        return str(vault.search(query) or "no matches")

    def memory_read(path: str) -> str:
        """Read one note from the vault.

        Args:
            path: Relative path such as projects/cydonia.md
        """
        try:
            return vault.read(path)
        except ValueError as e:
            return f"error: {e}"

    def memory_append(path: str, text: str) -> str:
        """Add a new fact to the end of an existing note. Prefer this over
        creating a new file. Only store durable facts, not chit-chat.

        Args:
            path: Relative path of the note.
            text: One short line, e.g. '- prefers dark HUD themes'
        """
        try:
            if not (vault.root / path).exists():
                return ("error: that note doesn't exist. Append to an existing note "
                        f"({', '.join(vault.list_files())}) or, only for a genuinely "
                        "new subject, create it with memory_write.")
            return vault.append(path, text)
        except ValueError as e:
            return f"error: {e}"

    def memory_write(path: str, content: str) -> str:
        """Create a note or fully rewrite one (replaces the whole file, so
        read it first if it exists).

        Args:
            path: Relative path of the note.
            content: Complete new Markdown content.
        """
        try:
            return vault.write(path, content)
        except ValueError as e:
            return f"error: {e}"

    def memory_replace(path: str, old: str, new: str) -> str:
        """Correct or update ONE fact in a note by swapping exact text.
        Use this to fix wrong facts instead of rewriting the file.

        Args:
            path: Relative path of the note.
            old: Exact existing text to replace.
            new: The corrected text.
        """
        try:
            return vault.replace(path, old, new)
        except ValueError as e:
            return f"error: {e}"

    def calculate_age(birthdate: str) -> str:
        """Get exact age today from a birthdate. Always use this instead of
        doing date math yourself.

        Args:
            birthdate: Date as YYYY-MM-DD
        """
        from datetime import date
        try:
            b = date.fromisoformat(birthdate)
        except ValueError:
            return "error: use YYYY-MM-DD"
        t = date.today()
        age = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
        return f"{age} years old (today is {t.isoformat()})"

    return [memory_search, memory_read, memory_append, memory_write,
            memory_replace, calculate_age]
