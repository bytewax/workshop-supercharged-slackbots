"""This module contains code for a demo document database (Qdrant vector database)."""

from PyPDF2 import PdfReader
import pathlib
from qdrant_client import QdrantClient


class DocumentDatabase:
    """A vector database for document storage and querying.

    Usage:
        # Create instance.
        db = DocumentDatabase()

        # Upload documents.
        db.upload_pdf_document("<path_to_document>")
        db.upload_txt_document("<path_to_txt_document>")

        # Search database.
        search_results = db.search("Windshield wipers.")

        print(search_results)
    """

    def __init__(self, model: str = "BAAI/bge-small-en-v1.5") -> None:
        """Initialize database."""
        self._client = QdrantClient(":memory:")

        self._client.set_model(model)
        self._index = 0

    def upload_pdf_document(
        self,
        file_path: str,
        chunk_length: int = 700,
        overlap: int = 200,
        document_name: str = "pdf_document",
    ) -> None:
        """Upload a pdf document to database.

        Args:
            file_path: Path to the document.
            chunk_length: Length of an individual chunk (character count).
            overlap: Overlap with between two chunks (character count).
            document_name: Name of the document.
        """
        reader = PdfReader(file_path)
        text = ""
        for i in range(len(reader.pages)):
            text += reader.pages[i].extract_text()
        self.upload_document_text(text, chunk_length, overlap, document_name)

    def upload_txt_document(
        self,
        file_path: str,
        chunk_length: int = 700,
        overlap: int = 200,
        document_name: str = "txt_document",
    ) -> None:
        """Upload a txt document to database.

        Args:
            file_path: Path to the document.
            chunk_length: Length of an individual chunk (character count).
            overlap: Overlap with between two chunks (character count).
            document_name: Name of the document.
        """
        text = ""
        with open(file_path, "r", encoding="utf-8") as file:
            text += file.read()
        self.upload_document_text(text, chunk_length, overlap, document_name)

    def upload_document_text(
        self,
        text: str,
        chunk_length: int = 700,
        overlap: int = 200,
        source: str = "document",
    ) -> None:
        """Upload document text to database.

        Args:
            text: Document contents as a string.
            chunk_length: Length of an individual chunk (character count).
            overlap: Overlap with between two chunks (character count).
            document_name: Name of the document.
        """
        chunks = []
        i = 0
        for i in range(chunk_length - overlap, len(text), chunk_length - overlap):
            chunks.append(text[i - (chunk_length - overlap) : i + overlap])
        if i < len(text) - 1:
            chunks.append(text[i:])

        metadata = [{"source": source} for _ in chunks]
        ids = [i for i in range(self._index, len(chunks) + self._index)]
        if ids:
            self._index = ids[-1] + 1
        self._client.add("document_chunks", chunks, metadata, ids)

    def upload_text_chapterwise(self, file_path: str):
        """Upload a text document by chunking it based on chapters."""
        chunks = pathlib.Path(file_path).read_text().split("\n\n")
        ids = [i for i in range(self._index, len(chunks) + self._index)]
        if ids:
            self._index = ids[-1] + 1
        metadata = [{"source": "document"} for _ in chunks]
        self._client.add("document_chunks", chunks, metadata, ids)

    def search(self, query: str, limit: int = 10) -> list[str]:
        """Search database."""
        return [
            res.document
            for res in self._client.query("document_chunks", query, limit=limit)
        ]
