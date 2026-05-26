import logging


log = logging.getLogger(__name__)

# Maximale PWM-Aufloesung des PCA9685.
# 0xFFFF entspricht 100 Prozent Einschaltdauer.
MAXIMALE_PWM_AUFLOESUNG = 0xFFFF


class MotorSteuerung:
    # Diese Klasse kapselt die komplette Motoransteuerung ueber den PCA9685.
    def __init__(self, pca, mindest_motor_geschwindigkeit):
        # Referenz auf das PWM-Modul.
        # Ueber dieses Objekt werden spaeter die einzelnen PWM-Kanaele gesetzt.
        self.pca = pca

        # Kleinster erlaubter Fahrwert fuer einen Motor.
        # Der Wert 0 bleibt weiterhin erlaubt, damit Motoren stoppen koennen.
        self.mindest_motor_geschwindigkeit = mindest_motor_geschwindigkeit

        # Gespeicherte aktuelle Sollgeschwindigkeiten der vier Motoren.
        # Diese Werte sind vor allem zum Debuggen hilfreich.
        self.aktuelle_geschwindigkeit_vorne_links = 0.0
        self.aktuelle_geschwindigkeit_vorne_rechts = 0.0
        self.aktuelle_geschwindigkeit_hinten_links = 0.0
        self.aktuelle_geschwindigkeit_hinten_rechts = 0.0

    def initialisieren(self):
        # Das PWM-Modul wird fuer Motorsteuerung initialisiert.
        # 100 Hz ist die verwendete PWM-Frequenz fuer diese Motorsteuerung.
        log.info("initialize the PWM module")
        self.pca.frequency = 100

        # Beim Start werden alle Motoren sicher ausgeschaltet.
        self.alle_stoppen()

    def alle_stoppen(self):
        # Alle acht verwendeten PWM-Kanaele auf 0 setzen.
        # Jeder Motor belegt zwei Kanaele: einen fuer jede Drehrichtung.
        for kanal in range(8):
            self.pca.channels[kanal].duty_cycle = 0

        # Interne Geschwindigkeitswerte ebenfalls zuruecksetzen.
        self.aktuelle_geschwindigkeit_vorne_links = 0.0
        self.aktuelle_geschwindigkeit_vorne_rechts = 0.0
        self.aktuelle_geschwindigkeit_hinten_links = 0.0
        self.aktuelle_geschwindigkeit_hinten_rechts = 0.0

    def _motor_setzen(self, vorwaerts_kanal, rueckwaerts_kanal, geschwindigkeit):
        # Diese Methode steuert genau einen Motor an.
        # Jeder Motor besitzt zwei PCA9685-Kanaele:
        # - ein Kanal fuer die eine Drehrichtung
        # - ein Kanal fuer die andere Drehrichtung
        #
        # geschwindigkeit > 0: Motor dreht in die eine Richtung
        # geschwindigkeit < 0: Motor dreht in die andere Richtung
        # geschwindigkeit = 0: beide Kanaele bekommen 0 Prozent PWM

        # Geschwindigkeit begrenzen, damit nur Werte von -100 bis +100
        # an die PWM-Berechnung weitergegeben werden.
        geschwindigkeit = self.geschwindigkeit_begrenzen(geschwindigkeit, -100, 100)

        # Sehr kleine PWM-Werte liefern bei Gleichstrommotoren oft zu wenig
        # Kraft, um sicher loszufahren. Deshalb wird jeder Fahrbefehl ungleich
        # 0 auf mindestens mindest_motor_geschwindigkeit angehoben.
        geschwindigkeit = self._mindestansteuerung_anwenden(geschwindigkeit)

        # Prozentwert in den 16-Bit-PWM-Wert des PCA9685 umrechnen.
        pwm_wert = int((abs(geschwindigkeit) * MAXIMALE_PWM_AUFLOESUNG) / 100)

        if geschwindigkeit >= 0:
            # Positive Geschwindigkeit: Rueckwaerts-Kanal aus,
            # Vorwaerts-Kanal mit berechnetem PWM-Wert ansteuern.
            self.pca.channels[vorwaerts_kanal].duty_cycle = 0
            self.pca.channels[rueckwaerts_kanal].duty_cycle = pwm_wert
        else:
            # Negative Geschwindigkeit: Vorwaerts-Kanal aus,
            # Rueckwaerts-Kanal mit berechnetem PWM-Wert ansteuern.
            self.pca.channels[vorwaerts_kanal].duty_cycle = pwm_wert
            self.pca.channels[rueckwaerts_kanal].duty_cycle = 0

        # Tatsaechlich verwendete Geschwindigkeit zurueckgeben.
        return geschwindigkeit

    def vorne_links(self, geschwindigkeit=0):
        # Vorderer linker Motor an PCA9685-Kanal 0 und 1.
        self.aktuelle_geschwindigkeit_vorne_links = self._motor_setzen(
            0,
            1,
            geschwindigkeit,
        )

    def hinten_links(self, geschwindigkeit=0):
        # Hinterer linker Motor an PCA9685-Kanal 2 und 3.
        self.aktuelle_geschwindigkeit_hinten_links = self._motor_setzen(
            2,
            3,
            geschwindigkeit,
        )

    def hinten_rechts(self, geschwindigkeit=0):
        # Hinterer rechter Motor an PCA9685-Kanal 4 und 5.
        self.aktuelle_geschwindigkeit_hinten_rechts = self._motor_setzen(
            4,
            5,
            geschwindigkeit,
        )

    def vorne_rechts(self, geschwindigkeit=0):
        # Vorderer rechter Motor an PCA9685-Kanal 6 und 7.
        self.aktuelle_geschwindigkeit_vorne_rechts = self._motor_setzen(
            6,
            7,
            geschwindigkeit,
        )

    def fahren(self, linke_geschwindigkeit, rechte_geschwindigkeit):
        # Gemeinsame Fahrfunktion fuer linke und rechte Fahrzeugseite.
        # Wegen der Einbaurichtung der Motoren muessen einzelne Motoren
        # mit umgekehrtem Vorzeichen angesteuert werden.
        #
        # Diese Funktion wird noch fuer die Suchbewegung benutzt.
        # Fuer normales Linienfolgen wird raeder_fahren() verwendet, weil dort
        # jedes Rad einzeln getrimmt werden kann.
        self.vorne_links(linke_geschwindigkeit)
        self.hinten_links(-linke_geschwindigkeit)
        self.vorne_rechts(-rechte_geschwindigkeit)
        self.hinten_rechts(rechte_geschwindigkeit)

    def raeder_fahren(
        self,
        vorne_links_geschwindigkeit,
        hinten_links_geschwindigkeit,
        vorne_rechts_geschwindigkeit,
        hinten_rechts_geschwindigkeit,
    ):
        # Einzelrad-Fahrfunktion. Hier koennen alle vier Raeder getrennt
        # angepasst werden, ohne die Motor-Kanalzuordnung zu veraendern.
        #
        # Die Vorzeichen sind absichtlich unterschiedlich:
        # Durch die mechanische Einbaurichtung drehen nicht alle Motoren bei
        # gleichem PWM-Vorzeichen in dieselbe Fahrtrichtung.
        self.vorne_links(vorne_links_geschwindigkeit)
        self.hinten_links(-hinten_links_geschwindigkeit)
        self.vorne_rechts(-vorne_rechts_geschwindigkeit)
        self.hinten_rechts(hinten_rechts_geschwindigkeit)

    @staticmethod
    def geschwindigkeit_begrenzen(wert, minimum, maximum):
        # Hilfsfunktion: begrenzt einen Wert auf einen erlaubten Bereich.
        return max(minimum, min(maximum, wert))

    def _mindestansteuerung_anwenden(self, geschwindigkeit):
        # 0 muss 0 bleiben, damit alle_stoppen() und bewusster Motorstopp
        # weiterhin funktionieren.
        if geschwindigkeit == 0:
            return 0

        if abs(geschwindigkeit) < self.mindest_motor_geschwindigkeit:
            if geschwindigkeit > 0:
                return self.mindest_motor_geschwindigkeit
            return -self.mindest_motor_geschwindigkeit

        return geschwindigkeit
