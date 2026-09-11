from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


@dataclass
class DocumentChunk:
    chunk_id: str
    source: str
    page: int
    content: str

    def to_dict(self) -> dict:
        return asdict(self)


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def split_text(text: str, max_chars: int = 700, overlap: int = 80) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 1 > max_chars:
            chunks.append(current)
            current = current[-overlap:] + "\n" + paragraph
        else:
            current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


def _read_pdf(path: Path) -> Iterable[tuple[int, str]]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        for page_number, page in enumerate(reader.pages, start=1):
            yield page_number, page.extract_text() or ""
        return
    except ImportError:
        pass
    except Exception as exc:
        raise RuntimeError(f"无法解析 PDF {path}: {exc}") from exc
    raise RuntimeError("解析 PDF 需要安装 pypdf")


def load_chunks(data_dir: Path) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    files = sorted(data_dir.glob("*.md")) + sorted(data_dir.glob("*.pdf"))
    for path in files:
        if path.suffix.lower() == ".md":
            pages = [(1, path.read_text(encoding="utf-8"))]
        else:
            pages = list(_read_pdf(path))
        for page, text in pages:
            for idx, content in enumerate(split_text(text)):
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{path.name}:{page}:{idx}",
                        source=path.name,
                        page=page,
                        content=content,
                    )
                )
    return chunks


class LocalIndex:
    """Deterministic lexical index used for the local demo and smoke tests."""

    def __init__(self, chunks: list[DocumentChunk]):
        self.chunks = chunks

    def search(self, query: str, top_k: int = 6) -> list[dict]:
        query_tokens = _tokens(query)
        scored = []
        for chunk in self.chunks:
            tokens = _tokens(chunk.content)
            overlap = len(query_tokens & tokens)
            phrase_bonus = 0.5 if query.strip() and query.strip() in chunk.content else 0
            score = overlap / max(len(query_tokens), 1) + phrase_bonus
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (item[0], item[1].source), reverse=True)
        return [
            {**item[1].to_dict(), "score": round(item[0], 4)}
            for item in scored[:top_k]
        ]

    def is_empty(self) -> bool:
        return not self.chunks

    def count(self) -> int:
        return len(self.chunks)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps([chunk.to_dict() for chunk in self.chunks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "LocalIndex":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls([DocumentChunk(**item) for item in data])


def build_local_index(data_dir: Path, output_path: Path) -> LocalIndex:
    index = LocalIndex(load_chunks(data_dir))
    index.save(output_path)
    return index
