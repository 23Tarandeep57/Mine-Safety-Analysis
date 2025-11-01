import io
from bs4 import BeautifulSoup
import requests
from pypdf import PdfReader
from .config import USER_AGENT

def _looks_like_pdf(content_type: str, url: str, content_sniff: bytes) -> bool:
    ct = (content_type or "").lower()
    if "application/pdf" in ct:
        return True
    if url.lower().endswith(".pdf"):
        return True
    return content_sniff.startswith(b"%PDF")


def _extract_text_from_pdf_bytes(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        texts = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            if t:
                texts.append(t)
        text = "\n".join(texts).strip()
        if len(text) < 200 and b"%%EOF" not in data:
            return "[Note: PDF appears to be truncated. Extraction may be incomplete.]\n" + text
        if len(text) < 200:
            return "[Note: PDF appears to contain little/no selectable text — possibly a scanned document. Extraction may be incomplete.]\n" + text
        return text
    except Exception as e:
        return f"[Error extracting PDF text: {e}]"


def extract_text_from_url(url: str, max_bytes: int = 0) -> str:
    headers = {"User-Agent": USER_AGENT}
    try:
        with requests.get(url, headers=headers, timeout=30, stream=True) as r:
            r.raise_for_status()
            content_type = r.headers.get("Content-Type", "")
            if max_bytes > 0:
                content = r.raw.read(max_bytes)
            else:
                content = r.content

            content_sniff = content[:8]
            if _looks_like_pdf(content_type, url, content_sniff):
                return _extract_text_from_pdf_bytes(content)
            
            text = content.decode("utf-8", errors="ignore")
            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            return text
    except Exception as e:
        return f"Error reading {url}: {e}"
