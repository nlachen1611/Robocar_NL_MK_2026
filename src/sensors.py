from gpiozero import LineSensor


class LinienSensoren:
    # Diese Klasse kapselt die drei digitalen Liniensensoren.
    def __init__(self):
        # Die Sensoren sind mittig vor dem Fahrzeug angeordnet.
        # Von Sensor zu Sensor betraegt der Abstand 1.5 cm.

        # Sensor links an GPIO 14.
        self.links = LineSensor(14)

        # Sensor in der Mitte an GPIO 15.
        self.mitte = LineSensor(15)

        # Sensor rechts an GPIO 23.
        self.rechts = LineSensor(23)

    def lesen(self):
        # Aktuelle Rohwerte der drei Sensoren lesen.
        # Rueckgabeformat: (links, mitte, rechts)
        return int(self.links.value), int(self.mitte.value), int(self.rechts.value)

    def schwarz_lesen(self, schwarz_wert):
        # Rohwerte in ein einheitliches Format umwandeln:
        # 1 bedeutet "Sensor sieht schwarz", 0 bedeutet "Sensor sieht nicht schwarz".
        #
        # Manche Sensor-Module liefern bei schwarz 1, andere bei schwarz 0.
        # Deshalb wird schwarz_wert in der Konfiguration festgelegt.
        werte = self.lesen()
        return tuple(1 if wert == schwarz_wert else 0 for wert in werte)
