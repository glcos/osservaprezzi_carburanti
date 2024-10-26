import hassapi as hass
import datetime
import re
from unicodedata import normalize
from mise import mise

FUEL_STATION_ID = 15890 # id stazione di servizio di esempio
DOWNLOAD_PATH = "/var/opt/carburanti/"
UPDATE_TIME_HOURS = 8
UPDATE_TIME_MINUTES = 30


class Carburanti(hass.Hass, mise):
    def initialize(self):
        self.runtime = datetime.time(UPDATE_TIME_HOURS, UPDATE_TIME_MINUTES, 0)
        self.run_daily(self.run_daily_update, self.runtime)

        self.mise = mise(FUEL_STATION_ID)
        self.mise.dl_path = DOWNLOAD_PATH
        self.run_daily_update()

    def slugify(self, text):
        slug = re.sub(r"(\w)['’](\w)", r"\1\2", text.lower())
        slug = re.sub(r"[\W_]+", "_", slug).strip("_")
        slug = normalize("NFKD", slug).encode("ascii", "ignore").decode()

        return slug

    def run_daily_update(self, *args):
        self.log("Aggiornamento giornaliero prezzi carburante")
        ret = self.mise.update()
        if ret:
            self.log("Prezzi carburante aggiornati con successo")
            self.update_sensors()
        else:
            self.log("Errore aggiornamento prezzi carburante")

    def update_sensors(self):
        csv_date = datetime.datetime.combine(self.mise.stations_ts, self.runtime)
        iso_ts = csv_date.isoformat()
        self.set_state(
            "sensor.stations_csv_last_updated",
            state=iso_ts,
            replace=True,
            attributes={
                "icon": "mdi:database-clock-outline",
                "friendly_name": "Stations CSV file last updated",
                "device_class": "timestamp",
            },
        )

        csv_date = datetime.datetime.combine(self.mise.price_ts, self.runtime)
        iso_ts = csv_date.isoformat()
        self.set_state(
            "sensor.price_csv_last_updated",
            state=iso_ts,
            replace=True,
            attributes={
                "icon": "mdi:database-clock-outline",
                "friendly_name": "Price CSV file last updated",
                "device_class": "timestamp",
            },
        )

        station_name = self.mise.station.name

        fuels = self.mise.fuels
        for fuel in fuels:
            fuel_desc = fuel.description + " " + fuel.experience
            station_id = fuel.station_id
            sensor = "sensor." + station_id + "_" + self.slugify(fuel_desc)
            price = fuel.price
            self.set_state(
                sensor,
                state=price,
                replace=True,
                attributes={
                    "icon": "mdi:cash-multiple",
                    "friendly_name": fuel_desc,
                    "unit_of_measurement": "€",
                    "state_class": "measurement",
                    "station_id": station_id,
                    "station_name": station_name,
                },
            )

    def logger(self, msg):
        self.log(msg)
