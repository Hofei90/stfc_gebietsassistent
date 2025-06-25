from flask import Flask, render_template, request
import toml
import utils
from datetime import datetime, timezone
import locale

app = Flask(__name__)

# TOML-Daten laden
data = toml.load("data.toml")

# Datums-Formatierungsfilter für UTC-Zeit
@app.template_filter('datetimeformat')
def datetimeformat(ts):


    dt = datetime.fromtimestamp(ts, tz=timezone.utc)

    # Sprache des Browsers lesen (z. B. "de-DE,de;q=0.9,en;q=0.8")
    lang_header = request.headers.get('Accept-Language', '')
    # Extrahiere primäre Sprache
    lang = lang_header.split(',')[0].replace('-', '_')  # z. B. "de_DE"

    try:
        # Versuche das passende Locale zu setzen
        locale.setlocale(locale.LC_TIME, f"{lang}.UTF-8")
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')  # Fallback

    return dt.strftime('%A, %d.%m.%Y %H:%M UTC')

def sort_table_data(table_data):
    return sorted(table_data, key=lambda x: x[3], reverse=False)

@app.route('/')
def index():
    table_data = []
    for entry in data["territories"]:
        ts = int(utils.get_target_ts(entry["date"]))
        table_data.append([
            entry["system"],        # 0
            entry["kategorie"],     # 1
            entry["ressource"],     # 2
            ts,                     # 3 - Unix Timestamp (UTC)
            entry["other_data"],    # 4
            bool(entry["priority"]) # 5
        ])

    table_data = sort_table_data(table_data)
    return render_template('index.html', table_data=table_data)

if __name__ == '__main__':
    app.run(debug=True)
