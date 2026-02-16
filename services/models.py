from dataclasses import dataclass

# -----------------------------
# Data models (optional)
# -----------------------------
@dataclass
class Note:
    id: str
    content: str


@dataclass
class SongPreview:
    id: str
    title: str
    artist: str
    album: str = "" 