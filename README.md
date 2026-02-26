# 🚀 Automatic LMStudio Webscraping → Notion

Dieses Projekt scrapt automatisch Webseiten oder APIs, fasst den Inhalt
mit einem lokalen LLM über **LM Studio** zusammen und speichert die
Ergebnisse direkt in einer Notion-Seite (z. B. „Scraping").

> ⚠️ Hinweis: Dieses Projekt ist aktuell ein **kleiner Testrun /
> Prototyp** und dient als Grundlage für weitere Erweiterungen. Viele
> Funktionen sind bewusst minimal gehalten und werden schrittweise
> ausgebaut.

------------------------------------------------------------------------

## ✨ Features

-   🌐 Web Scraping für HTML-Seiten & JSON-APIs\
-   🧠 Lokale KI-Zusammenfassung via LM Studio\
-   📰 Automatische Inhalts-Extraktion (readability + BeautifulSoup)\
-   🧩 Unterstützung langer Texte durch Chunking + Map-Reduce
    Summarization\
-   📝 Direkte Speicherung der Zusammenfassung in Notion

------------------------------------------------------------------------

## 🧰 Voraussetzungen

Bevor du startest, stelle sicher, dass folgendes vorhanden ist:

-   Python **3.10+**
-   Installiertes **LM Studio** + geladenes Modell (z. B.
    `qwen/qwen3-vl-4b`)
-   Notion Integration + API Token
-   Eine Notion-Seite (z. B. **„Scraping"**), die für die Integration
    freigegeben ist

------------------------------------------------------------------------

## ⚙️ Installation

``` bash
git clone <repo>
cd <repo>
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 🔑 Konfiguration

Passe die Werte in deinem `main.py` an:

``` python
LM_MODEL_ID = "qwen/qwen3-vl-4b"
NOTION_TOKEN = "your_notion_token"
NOTION_PAGE_ID = "your_notion_page_id"

URLS = [
    "https://api.open-meteo.com/v1/forecast?latitude=53.0752&longitude=8.80777&current_weather=true"
]
```

### ❗ Wichtig

Die Notion-Seite muss für die Integration freigegeben sein:

1.  Notion öffnen\
2.  Seite „Scraping" auswählen\
3.  **Share** → Integration hinzufügen

------------------------------------------------------------------------

## ▶️ Starten

``` bash
python main.py
```

------------------------------------------------------------------------

## 🌍 Unterstützte Quellen

### 📰 Webseiten

-   Blogs\
-   Wikipedia\
-   Dokumentationen\
-   News-Seiten

### ⚡ APIs (empfohlen für schnelle Tests)

Beispiel: Wetterdaten für Bremen

    https://api.open-meteo.com/v1/forecast?latitude=53.0752&longitude=8.80777&current_weather=true

APIs liefern kleine JSON-Daten → sehr schnelle Verarbeitung ⚡

------------------------------------------------------------------------

## 🧠 Funktionsweise

1.  URL abrufen (`requests`)
2.  Hauptinhalt extrahieren (`readability` + `BeautifulSoup`)
3.  Text bereinigen & normalisieren
4.  Text in Chunks aufteilen (wegen LLM-Kontextlimit)
5.  Map-Reduce Zusammenfassung mit LM Studio
6.  Ergebnis in der Notion-Seite „Scraping" speichern

------------------------------------------------------------------------

## ⚠️ Hinweise & Bekannte Punkte

-   Dieses Projekt ist aktuell ein **Proof-of-Concept / Testrun**\
-   Die Architektur ist bewusst modular gehalten und **vollständig
    erweiterbar**
-   Weitere Features (Scheduling, Diff-Erkennung, DB-Integration) sind
    geplant

### RequestsDependencyWarning

Beim Ausführen kann folgende Warnung auftreten:

    RequestsDependencyWarning: urllib3 (...) or chardet (...)/charset_normalizer (...) doesn't match a supported version!
    warnings.warn(

Diese Warnung entsteht durch Versionskonflikte in der Python-Umgebung
(meist `requests`, `urllib3`, `charset-normalizer`). Sie beeinflusst die
Funktionalität in der Regel **nicht kritisch**, wird aber aktuell noch
bereinigt und optimiert.

Empfohlene Lösung langfristig: - Saubere virtuelle Umgebung (`venv` oder
Conda) - Konsistente Installation über `requirements.txt`

------------------------------------------------------------------------

## 🔮 Mögliche Erweiterungen

-   ⏰ Automatisches zeitgesteuertes Scraping (Cron / Task Scheduler)
-   📊 Speicherung in einer Notion-Datenbank statt Seite
-   🔍 Diff-Erkennung bei Änderungen von Webseiten
-   🧠 Multi-Model Support für verschiedene Summarization-Strategien
-   📡 Unterstützung mehrerer Datenquellen & APIs

------------------------------------------------------------------------

## 🛡️ Sicherheit

Gehe sorgsam mit deinen Tokens um!

------------------------------------------------------------------------

Viel Spaß beim automatischen Web-Scraping & KI-Zusammenfassen! 🚀
