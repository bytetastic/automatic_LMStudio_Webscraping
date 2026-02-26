import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document
import lmstudio as lms
from notion_client import Client


# -----------------------------
# Konfiguration
# -----------------------------
LM_MODEL_ID = "qwen/qwen3-vl-4b" # Nutze dieses LLM oder eins nach deinem Wunsch

# Für den Anfang hardcodiert (später besser via .env)
NOTION_TOKEN = "Dein_Notion_Token"
NOTION_PAGE_ID = "Deine_Notion_Page_ID"  # Page "Scraping" ID

# Ziel-URLs
URLS = [
    "https://api.open-meteo.com/v1/forecast?latitude=53.0752&longitude=8.80777&current_weather=true",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NotionSummarizer/1.0)"
}

# LLM-Kontext ist bei dir n_ctx=4096 => wir müssen chunking machen
CHUNK_SIZE = 2800       # Zeichen pro Chunk (safe für 4k ctx)
CHUNK_OVERLAP = 200     # Überlappung, damit Sätze nicht hart abbrechen

# Notion Limits
NOTION_TEXT_CHUNK = 1800


# -----------------------------
# Helpers
# -----------------------------
def validate_url(url: str) -> None:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.netloc:
        raise ValueError(f"Ungültige URL: {url}")


def clean_text(text: str) -> str:
    # typische Noise-Reduktion (u.a. Wikipedia Referenzen)
    text = re.sub(r"\[\d+]", "", text)  # [1], [2], ...
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_into_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if size <= overlap:
        raise ValueError("CHUNK_SIZE muss größer als CHUNK_OVERLAP sein.")

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap

    return chunks


def fetch_article(url: str) -> dict:
    """Fetch + extract main content from a webpage."""
    validate_url(url)

    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    doc = Document(r.text)
    title = doc.short_title() or "Ohne Titel"

    html = doc.summary(html_partial=True)
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)

    # Fallback: wenn readability zu wenig liefert
    if len(text) < 400:
        soup2 = BeautifulSoup(r.text, "lxml")
        if soup2.title:
            title = soup2.title.get_text(strip=True)

        ps = [p.get_text(" ", strip=True) for p in soup2.find_all("p")]
        text = "\n".join([p for p in ps if len(p) > 40])

    text = clean_text(text)
    if not text:
        raise RuntimeError(f"Kein Text extrahiert aus: {url}")

    return {"title": title, "content": text}


# -----------------------------
# LLM (Map-Reduce Summarization)
# -----------------------------
def llm_respond(prompt: str) -> str:
    model = lms.llm(LM_MODEL_ID)
    resp = model.respond(prompt)
    return str(resp)


def summarize_chunk(chunk: str, idx: int, total: int, url: str | None = None) -> str:
    prompt = (
        "Fasse den folgenden Abschnitt knapp und faktisch in Stichpunkten zusammen.\n"
        "Regeln:\n"
        "- Maximal 8 Bulletpoints\n"
        "- Keine Spekulationen / keine neuen Fakten\n"
        "- Wichtige Begriffe/Definitionen beibehalten\n"
        f"- Abschnitt {idx}/{total}\n"
    )
    if url:
        prompt += f"Quelle: {url}\n"

    prompt += f"\nABSCHNITT:\n{chunk}"
    return llm_respond(prompt)


def reduce_summaries(chunk_summaries: list[str], title: str, url: str | None = None) -> str:
    joined = "\n\n".join(chunk_summaries)

    prompt = (
        f"Du bekommst Teil-Zusammenfassungen eines Textes mit dem Titel: {title}\n"
        "Erstelle daraus eine finale, strukturierte Zusammenfassung auf Deutsch.\n\n"
        "Struktur:\n"
        "1) Key Takeaways (5-8 Punkte)\n"
        "2) Hauptthemen (mit Unterpunkten)\n"
        "3) Offene Fragen / ToDos\n\n"
        "Regeln:\n"
        "- Keine Halluzinationen: nur Inhalte verwenden, die in den Teil-Zusammenfassungen stehen\n"
        "- Prägnant, aber vollständig\n"
    )
    if url:
        prompt += f"\nQuelle: {url}\n"

    prompt += f"\nTEIL-ZUSAMMENFASSUNGEN:\n{joined}"
    return llm_respond(prompt)


def summarize_text_map_reduce(text: str, title: str, url: str | None = None) -> str:
    chunks = split_into_chunks(text)
    summaries = []

    for i, ch in enumerate(chunks, start=1):
        print(f"  - Summarize Chunk {i}/{len(chunks)} (chars={len(ch)})")
        summaries.append(summarize_chunk(ch, i, len(chunks), url=url))

    print("  - Reduce to final summary")
    return reduce_summaries(summaries, title=title, url=url)


# -----------------------------
# Notion
# -----------------------------
def notion_rich_text(content: str):
    return [{"type": "text", "text": {"content": content}}]


def send_to_notion_toggle(title: str, url: str, summary: str) -> None:
    """
    Fügt unter der Seite NOTION_PAGE_ID einen Toggle hinzu:
    ▶ Titel
        Quelle: ...
        Zusammenfassung...
    """
    notion = Client(auth=NOTION_TOKEN)

    parts = [summary[i:i + NOTION_TEXT_CHUNK] for i in range(0, len(summary), NOTION_TEXT_CHUNK)]

    toggle_children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": notion_rich_text(f"Quelle: {url}")}
        }
    ]

    for part in parts:
        toggle_children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": notion_rich_text(part)}
        })

    children = [
        {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": notion_rich_text(title),
                "children": toggle_children
            }
        }
    ]

    notion.blocks.children.append(NOTION_PAGE_ID, children=children)


# -----------------------------
# Main
# -----------------------------
def main():
    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        raise RuntimeError("NOTION_TOKEN / NOTION_PAGE_ID fehlen (aktuell hardcodiert erwartet).")

    if not URLS:
        raise RuntimeError("URLS ist leer. Bitte mindestens eine URL eintragen.")

    for url in URLS:
        try:
            print(f"\n--- Verarbeite: {url}")
            article = fetch_article(url)
            print(f"Title: {article['title']}")
            print(f"Text length: {len(article['content'])} chars")

            summary = summarize_text_map_reduce(article["content"], title=article["title"], url=url)

            send_to_notion_toggle(article["title"], url, summary)
            print("-> In Notion (Seite 'Scraping') hinzugefügt.")
        except Exception as e:
            print(f"!! Fehler bei {url}: {e}")

    print("\nFertig.")


if __name__ == "__main__":
    main()