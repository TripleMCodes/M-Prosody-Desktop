from dataclasses import dataclass
from typing import Optional

# -----------------------------
# Data models (optional)
# -----------------------------
@dataclass
class Note:
    id: str
    content: str
    created_at: Optional[str] = None
    update_at: Optional[str] = None


@dataclass
class SongPreview:
    id: str
    title: str
    artist: str
    album: str = "" 