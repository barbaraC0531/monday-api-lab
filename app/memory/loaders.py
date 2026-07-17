from pathlib import Path


def load_markdown(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


class MemoryLoader:
    def __init__(self, persona_path: Path, stable_memory_path: Path) -> None:
        self.persona_path = persona_path
        self.stable_memory_path = stable_memory_path

    def load_persona(self) -> str:
        return load_markdown(self.persona_path)

    def load_stable_memory(self) -> str:
        return load_markdown(self.stable_memory_path)

    def status(self) -> dict[str, bool | str]:
        return {
            "persona_path": str(self.persona_path),
            "persona_loaded": bool(self.load_persona()),
            "stable_memory_path": str(self.stable_memory_path),
            "stable_memory_loaded": bool(self.load_stable_memory()),
        }
