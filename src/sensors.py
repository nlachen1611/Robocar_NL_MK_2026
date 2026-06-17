from dataclasses import dataclass

from gpiozero import LineSensor


GPIO_SENSOR_LINKS = 14
GPIO_SENSOR_MITTE = 15
GPIO_SENSOR_RECHTS = 23


@dataclass(frozen=True)
class SensorWerte:
    links: int
    mitte: int
    rechts: int

    def anzahl_aktiver_sensoren(self):
        return self.links + self.mitte + self.rechts


class LinienSensoren:
    def __init__(self, schwarz_wert):
        self.schwarz_wert = schwarz_wert
        self.sensor_links = LineSensor(GPIO_SENSOR_LINKS)
        self.sensor_mitte = LineSensor(GPIO_SENSOR_MITTE)
        self.sensor_rechts = LineSensor(GPIO_SENSOR_RECHTS)

    def schwarz_lesen(self):
        return SensorWerte(
            links=self._erkennt_schwarz(self.sensor_links),
            mitte=self._erkennt_schwarz(self.sensor_mitte),
            rechts=self._erkennt_schwarz(self.sensor_rechts),
        )

    def _erkennt_schwarz(self, sensor):
        return int(sensor.value == self.schwarz_wert)
