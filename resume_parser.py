from pathlib import Path

def load_resume(path: str) -> str:
    """Load resume text from a file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return p.read_text()
