from pathlib import Path

class KnowledgeBase:
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self._full_text = ""
        self._load_all()

    def _load_all(self):
        if not self.knowledge_dir.exists():
            print(f"⚠️ Папка {self.knowledge_dir} не найдена.")
            return
        for file_path in sorted(self.knowledge_dir.rglob("*.txt")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                    if text:
                        relative_path = file_path.relative_to(self.knowledge_dir)
                        self._full_text += f"\n=== {relative_path} ===\n"
                        self._full_text += text + "\n"
            except Exception as e:
                print(f"Ошибка загрузки {file_path}: {e}")

    def search(self, query: str) -> str:
        return self._full_text

    def reload(self):
        self._full_text = ""
        self._load_all()

# Глобальный экземпляр для использования в других модулях
knowledge_base = KnowledgeBase()