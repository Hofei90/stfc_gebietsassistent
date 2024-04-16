from flask import Flask, render_template
import toml

import utils

app = Flask(__name__)

# Lesen der Daten aus der TOML-Datei
data = toml.load("data.toml")  # Annahme, dass die TOML-Datei "daten.tml" heißt


def sort_table_data(table_data):
    return sorted(table_data, key=lambda x: x[4], reverse=False)


@app.route('/')
def index():
    # Erzeugen der Tabelle
    table_data = []
    for entry in data["territories"]:
        time_string = entry['date']
        remaining_time = utils.get_remaining_time(time_string)
        table_data.append([
            entry["system"],
            entry["kategorie"],
            entry["ressource"],
            entry["date"],
            remaining_time,
            entry["other_data"],
            bool(entry["priority"])
        ])

    # Sortieren der Tabelle nach der verbleibenden Zeit
    table_data = sort_table_data(table_data)
    return render_template('index.html', table_data=table_data)


if __name__ == '__main__':
    app.run(debug=True)

