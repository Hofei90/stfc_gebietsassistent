# stfc_gebietsassistent

## Admin-Bot (Gebiete über Discord verwalten)

`gebietsassistent_admin_dc.py` ist ein dauerhaft laufender Discord-Bot, mit dem Mitglieder mit der
Admin-Rolle die Gebiete in `data.toml` per Slash-Befehl verwalten können:

| Befehl | Funktion |
|---|---|
| `/gebiet_liste` | alle Gebiete anzeigen |
| `/gebiet_neu` | neues Gebiet anlegen |
| `/gebiet_aendern` | Kategorie, Ressource, Wochentag, Uhrzeit oder sonstige Daten ändern |
| `/gebiet_aktivieren` | Erinnerung aktivieren (`priority = 1`) |
| `/gebiet_deaktivieren` | Erinnerung deaktivieren (`priority = 0`) |

Gebiete können absichtlich nicht gelöscht werden. Uhrzeiten sind wie bisher in UTC.

### Zusätzliche Einträge in `config.toml`

```toml
guild_id = 123456789012345678          # ID des eigenen Discord-Servers (Befehle nur dort)
admin_role = "Gebietsadmin"            # nur Mitglieder mit dieser Rolle dürfen ändern
admin_channel = "gebiet-admin"         # optional: Befehle nur in diesem Kanal erlaubt
restart_command = ["sudo", "systemctl", "restart", "gebietsassistent"]  # optional
```

`restart_command` startet nach jeder Änderung `gebietsassistent_control.py` neu, damit die neuen
Daten übernommen werden. Bei `sudo` sollte in den sudoers nur genau dieser eine Befehl ohne
Passwort erlaubt werden. Fehlt der Eintrag, muss der Gebietsassistent manuell neu gestartet werden.

### Sicherheit

- Berechtigung: nur im eingestellten Server, nur mit der Admin-Rolle (und ggf. nur im Admin-Kanal).
- Antworten sind nur für den Aufrufer sichtbar und lösen keine Pings aus.
- Eingaben werden geprüft (Wochentag, Uhrzeit, Längen, keine Zeilenumbrüche, keine doppelten Systeme).
- `data.toml` wird über eine Temp-Datei geschrieben, vorher geprüft und erst dann ausgetauscht.
  Die vorherige Version liegt in `data.toml.bak`. Kommentare in `data.toml` bleiben erhalten.
- Jede Änderung und jeder abgelehnte Versuch wird in `gebietsassistent_admin.log` protokolliert.
