from pathlib import Path


class IceFileManager:
    def __init__(
        self,
        base_dir=None,
        file_suffix=".ice",
        ignore_dirs: set | None = None,
        ignore_files: set = set(),
    ):
        self.base_dir = Path(base_dir or Path(__file__).resolve().parent.parent)
        self.search_path = self.base_dir / "test"
        self.file_suffix = file_suffix
        self.ignore_dirs = ignore_dirs or {"__pycache__"}
        self.ignore_files = ignore_files

    def _get_dirs(self):
        return [self.search_path] + [
            p
            for p in self.search_path.iterdir()
            if p.is_dir() and p.name not in self.ignore_dirs
        ]

    def find_all_files(self):
        """Generator für (Pfad, Inhalt)-Tupel"""
        for directory in self._get_dirs():
            for file in directory.glob(f"*{self.file_suffix}"):
                if file not in self.ignore_files:
                    yield file, file.read_text(encoding="utf-8")

    def read_all_files(self, verbose=False):
        """Liest alle Dateien als Liste von (Pfad, Inhalt)"""
        files = []
        for file, content in self.find_all_files():
            files.append((file, content))
            if verbose:
                print(f"\n--- {file} ---\n{content}")
        return files

    def read_file_by_path(self, filepath, verbose=False):
        for file, content in self.find_all_files():
            if file == filepath:
                if verbose:
                    print(f"{filepath} wird bearbeitet...\n{content}")
                return content
        return None
