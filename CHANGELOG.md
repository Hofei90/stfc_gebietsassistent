# Changelog

Alle bemerkenswerten Änderungen an diesem Projekt werden in diesem Dokument festgehalten.

Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/)
und folgt möglichst den [SemVer](https://semver.org/lang/de/) Regeln.

## [Unreleased]

### Hinzugefügt
- Unterstützung für `<t:timestamp>`-Format zur Discord-Zeitformatierung
- Lokale Zeitanzeige im Web-Frontend via JavaScript (aus UTC)
- Rollenprüfung im Discord-Bot mit Abbruch bei Fehler
- favicon.ico, PNGs und manifest für Browser

### Geändert
- `utils.py`: Zeitberechnung vollständig UTC-basiert, keine Local-TZ-Umwandlung mehr
- Discord-Bot: ersetzt `SystemExit` durch sauberen Shutdown
- Webanzeige verwendet Unix-Timestamps statt verbleibende Millisekunden

### Entfernt
- Naive Zeitberechnungen (`utcnow().replace(...)`)
