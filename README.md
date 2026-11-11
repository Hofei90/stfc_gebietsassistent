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
| `/gebiet_neustart` | Gebietsassistent neu starten, damit Änderungen wirksam werden |

Gebiete können absichtlich nicht gelöscht werden. Uhrzeiten sind wie bisher in UTC.

### Zusätzliche Einträge in `config.toml`

```toml
guild_id = 123456789012345678          # ID des eigenen Discord-Servers (Befehle nur dort)
admin_role = "Gebietsadmin"            # nur Mitglieder mit dieser Rolle dürfen ändern
admin_channel = "gebiet-admin"         # optional: Befehle nur in diesem Kanal erlaubt
restart_command = ["sudo", "-n", "/usr/bin/systemctl", "restart", "gebietsassistent.service"]  # optional
```

Änderungen werden nur in `data.toml` gespeichert. Wirksam werden sie erst, wenn
`gebietsassistent_control.py` neu gestartet wird. Das geschieht bewusst und nur über `/gebiet_neustart`,
der einmalig `restart_command` ausführt. Bei `sudo` sollte in den sudoers nur genau dieser eine Befehl
ohne Passwort erlaubt werden. Fehlt der Eintrag, muss der Gebietsassistent manuell neu gestartet werden.

### Sichtbarkeit der Befehle

Die Befehle sind standardmäßig nur für Server-Administratoren sichtbar. Damit die Admin-Rolle sie
sieht: Servereinstellungen → Integrationen → Bot → Befehle, dort die Rolle (und optional den Kanal)
freigeben. Die Rollenprüfung im Bot bleibt zusätzlich bestehen.

### Sicherheit

- Berechtigung: nur im eingestellten Server, nur mit der Admin-Rolle (und ggf. nur im Admin-Kanal).
- Antworten sind nur für den Aufrufer sichtbar und lösen keine Pings aus.
- Eingaben werden geprüft (Wochentag, Uhrzeit, Längen, keine Zeilenumbrüche, keine doppelten Systeme).
- `data.toml` wird über eine Temp-Datei geschrieben, vorher geprüft und erst dann ausgetauscht.
  Die vorherige Version liegt in `data.toml.bak`. Kommentare in `data.toml` bleiben erhalten.
- Jede Änderung und jeder abgelehnte Versuch wird in `gebietsassistent_admin.log` protokolliert.

## Betrieb mit systemd

Im Ordner `systemd/` liegen zwei Service-Dateien und eine sudoers-Regel. Benutzer (`stfc`) und Pfade
(`/home/stfc/stfc_gebietsassistent`, `venv`) vorher an die eigene Installation anpassen.

```bash
# Service-Dateien installieren
sudo cp systemd/gebietsassistent.service systemd/gebietsassistent_admin.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gebietsassistent.service gebietsassistent_admin.service

# sudoers-Regel für /gebiet_neustart (Inhalt aus systemd/sudoers_gebietsassistent einfügen)
sudo visudo -f /etc/sudoers.d/gebietsassistent

# Status und Ausgaben ansehen
systemctl status gebietsassistent.service
journalctl -u gebietsassistent_admin.service -f
```

Der Eintrag `restart_command` in `config.toml` muss exakt zur sudoers-Regel passen
(`sudo -n /usr/bin/systemctl restart gebietsassistent.service`). Die Regel erlaubt nur genau
diesen einen Befehl, `-n` verhindert, dass der Bot auf eine Passwortabfrage wartet.
