import logging
import signal
import time

import board
from adafruit_pca9685 import PCA9685
from gpiozero import LineSensor

# Grundeinstellung fuer die Log-Ausgabe.
# INFO zeigt wichtige Start-/Stopp-Meldungen an.
# Fuer genauere Reglerwerte kann level=logging.DEBUG verwendet werden.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)


# Maximale PWM-Aufloesung des PCA9685.
# 0xFFFF entspricht 100 Prozent Einschaltdauer.
MAX_DUTY_CYCLE = 0xFFFF


class LineFollowerConfig:
    # Diese Klasse enthaelt alle Einstellwerte fuer den Linienfolger.
    # Sie ist bewusst ohne @dataclass und ohne moderne Variablen-Typangaben
    # geschrieben, damit sie auch auf aelteren Raspberry-Pi-Python-Versionen
    # stabil laeuft.
    def __init__(self):
        # Grundgeschwindigkeit, mit der das Fahrzeug geradeaus faehrt.
        self.base_speed = 30.0

        # Maximale erlaubte Motorgeschwindigkeit.
        # Dadurch kann die Regelung die Motoren nicht zu stark ansteuern.
        self.max_speed = 100.0

        # P-Anteil der Regelung.
        # Je groesser kp ist, desto staerker reagiert das Fahrzeug auf
        # Abweichungen von der Linie.
        self.kp = 10.0

        # D-Anteil der Regelung.
        # Dieser Anteil reagiert auf schnelle Aenderungen des Fehlers und
        # beruhigt dadurch das Lenkverhalten.
        self.kd = 15.0

        # Feineinstellung fuer ungleich starke Motorseiten.
        # Wenn das Auto auf der Geraden nach links zieht, right_trim erhoehen
        # oder left_trim senken.
        # Wenn das Auto auf der Geraden nach rechts zieht, left_trim erhoehen
        # oder right_trim senken.
        self.left_trim = 1.0
        self.right_trim = 1.0

        # Pause zwischen zwei Regelungsdurchlaeufen in Sekunden.
        # 0.03 Sekunden entsprechen etwa 33 Messungen pro Sekunde.
        self.loop_delay = 0.03

        # Geschwindigkeit, mit der sich das Fahrzeug dreht, wenn keine Linie
        # erkannt wird.
        self.search_speed = 35.0

        # Wert, den die LineSensoren liefern, wenn sie schwarz erkennen.
        # Falls die Sensoren umgekehrt arbeiten, muss dieser Wert auf 0
        # gesetzt werden.
        self.black_value = 1


class MotorController:
    # Diese Klasse kapselt die komplette Motoransteuerung ueber den PCA9685.
    def __init__(self, pca):
        # Referenz auf das PWM-Modul.
        self.pca = pca

        # Gespeicherte aktuelle Sollgeschwindigkeiten der vier Motoren.
        # Diese Werte sind vor allem zum Debuggen hilfreich.
        self.current_speed_front_left = 0.0
        self.current_speed_front_right = 0.0
        self.current_speed_rear_left = 0.0
        self.current_speed_rear_right = 0.0

    def init(self):
        # Das PWM-Modul wird fuer Motorsteuerung initialisiert.
        # 100 Hz ist die verwendete PWM-Frequenz fuer diese Motorsteuerung.
        log.info("initialize the PWM module")
        self.pca.frequency = 100

        # Beim Start werden alle Motoren sicher ausgeschaltet.
        self.stop_all()

    def stop_all(self):
        # Alle acht verwendeten PWM-Kanaele auf 0 setzen.
        # Jeder Motor belegt zwei Kanaele: einen fuer jede Drehrichtung.
        for channel in range(8):
            self.pca.channels[channel].duty_cycle = 0

        # Interne Geschwindigkeitswerte ebenfalls zuruecksetzen.
        self.current_speed_front_left = 0.0
        self.current_speed_front_right = 0.0
        self.current_speed_rear_left = 0.0
        self.current_speed_rear_right = 0.0

    def _set_motor(self, forward_channel, backward_channel, speed):
        # Geschwindigkeit begrenzen, damit nur Werte von -100 bis +100
        # an die PWM-Berechnung weitergegeben werden.
        speed = self._limit_speed(speed, -100, 100)

        # Prozentwert in den 16-Bit-PWM-Wert des PCA9685 umrechnen.
        motor_speed = int((abs(speed) * MAX_DUTY_CYCLE) / 100)

        if speed >= 0:
            # Positive Geschwindigkeit: Rueckwaerts-Kanal aus,
            # Vorwaerts-Kanal mit berechnetem PWM-Wert ansteuern.
            self.pca.channels[forward_channel].duty_cycle = 0
            self.pca.channels[backward_channel].duty_cycle = motor_speed
        else:
            # Negative Geschwindigkeit: Vorwaerts-Kanal aus,
            # Rueckwaerts-Kanal mit berechnetem PWM-Wert ansteuern.
            self.pca.channels[forward_channel].duty_cycle = motor_speed
            self.pca.channels[backward_channel].duty_cycle = 0

        # Tatsaechlich verwendete Geschwindigkeit zurueckgeben.
        return speed

    def front_left(self, speed=0):
        # Vorderer linker Motor an PCA9685-Kanal 0 und 1.
        self.current_speed_front_left = self._set_motor(0, 1, speed)

    def rear_left(self, speed=0):
        # Hinterer linker Motor an PCA9685-Kanal 2 und 3.
        self.current_speed_rear_left = self._set_motor(2, 3, speed)

    def rear_right(self, speed=0):
        # Hinterer rechter Motor an PCA9685-Kanal 4 und 5.
        self.current_speed_rear_right = self._set_motor(4, 5, speed)

    def front_right(self, speed=0):
        # Vorderer rechter Motor an PCA9685-Kanal 6 und 7.
        self.current_speed_front_right = self._set_motor(6, 7, speed)

    def drive(self, left_speed, right_speed):
        # Gemeinsame Fahrfunktion fuer linke und rechte Fahrzeugseite.
        # Wegen der Einbaurichtung der Motoren muessen einzelne Motoren
        # mit umgekehrtem Vorzeichen angesteuert werden.
        self.front_left(left_speed)
        self.rear_left(-left_speed)
        self.front_right(-right_speed)
        self.rear_right(right_speed)

    @staticmethod
    def _limit_speed(value, minimum, maximum):
        # Hilfsfunktion: begrenzt einen Wert auf einen erlaubten Bereich.
        return max(minimum, min(maximum, value))


class LineSensors:
    # Diese Klasse kapselt die drei digitalen Liniensensoren.
    def __init__(self):
        # Sensor links an GPIO 14.
        self.left = LineSensor(14)

        # Sensor in der Mitte an GPIO 15.
        self.middle = LineSensor(15)

        # Sensor rechts an GPIO 23.
        self.right = LineSensor(23)

    def read(self):
        # Aktuelle Rohwerte der drei Sensoren lesen.
        # Rueckgabeformat: (links, mitte, rechts)
        return int(self.left.value), int(self.middle.value), int(self.right.value)

    def read_black(self, black_value):
        # Rohwerte in ein einheitliches Format umwandeln:
        # 1 bedeutet "Sensor sieht schwarz", 0 bedeutet "Sensor sieht nicht schwarz".
        values = self.read()
        return tuple(1 if value == black_value else 0 for value in values)


class LineFollower:
    # Diese Klasse enthaelt die eigentliche Linienfolger-Regelung.
    def __init__(self, motors, sensors, config):
        # Motorsteuerung, Sensoren und Einstellwerte speichern.
        self.motors = motors
        self.sensors = sensors
        self.config = config

        # Letzter Regelfehler fuer den D-Anteil der Regelung.
        self.last_error = 0.0

        # Letzte bekannte Linienrichtung.
        # Diese wird verwendet, wenn die Linie kurz verloren geht.
        self.last_line_error = 0.0

        # Laufvariable fuer die Hauptschleife.
        self.running = True

    def stop(self, *_):
        # Wird bei Strg+C oder beim Beenden des Programms aufgerufen.
        self.running = False

    def follow_forever(self):
        # Signalhandler registrieren, damit die Motoren beim Beenden
        # sauber ausgeschaltet werden.
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        log.info("start line follower")
        try:
            # Hauptschleife: Sensoren lesen, Fehler berechnen, Motoren ansteuern.
            while self.running:
                # Sensoren als Schwarz-Erkennung lesen.
                sensor_values = self.sensors.read_black(self.config.black_value)

                # Aus den Sensorwerten wird ein Linienfehler berechnet.
                error = self._line_error(sensor_values)

                if error is None:
                    # Keine Linie erkannt: Fahrzeug sucht die Linie wieder.
                    self._search_line()
                else:
                    # Linie erkannt: normale Regelung ausfuehren.
                    self._follow_line(error)

                # Kurze Pause, damit die Schleife kontrolliert laeuft.
                time.sleep(self.config.loop_delay)
        finally:
            # Dieser Block wird auch bei Fehlern oder Strg+C ausgefuehrt.
            # Dadurch bleiben die Motoren nicht unbeabsichtigt eingeschaltet.
            log.info("stop motors")
            self.motors.stop_all()

    def _line_error(self, values):
        # Sensorwerte auf einzelne Namen aufteilen.
        left, middle, right = values

        # Anzahl der Sensoren, die gerade schwarz erkennen.
        active_count = left + middle + right

        if active_count == 0:
            # Kein Sensor sieht die Linie.
            # Die Regelung kann dann keinen exakten Fehler berechnen.
            return None

        # Gewichtete Fehlerberechnung:
        # links  = -1
        # mitte  =  0
        # rechts = +1
        #
        # Beispiele:
        # (0, 1, 0) ->  0.0  Linie ist mittig
        # (1, 0, 0) -> -1.0  Linie liegt links
        # (0, 0, 1) -> +1.0  Linie liegt rechts
        # (1, 1, 0) -> -0.5  Linie liegt leicht links
        error = ((-1.0 * left) + (0.0 * middle) + (1.0 * right)) / active_count

        # Letzte bekannte Linienposition speichern.
        self.last_line_error = error
        return error

    def _follow_line(self, error):
        # Aenderung des Fehlers seit dem letzten Schleifendurchlauf.
        # Dieser Wert bildet den D-Anteil.
        derivative = error - self.last_error

        # Wenn die Linie genau in der Mitte liegt, soll das Fahrzeug ruhig
        # geradeaus fahren. Ohne diese Sonderbehandlung kann der D-Anteil nach
        # einer vorherigen Korrektur noch kurz gegenlenken und Pendeln erzeugen.
        if error == 0:
            correction = 0.0
            derivative = 0.0
        else:
            # PD-Regler:
            # P-Anteil: aktueller Fehler
            # D-Anteil: Aenderung des Fehlers
            # Das Ergebnis ist die Lenk-Korrektur.
            correction = (self.config.kp * error) + (self.config.kd * derivative)

        # Die Korrektur wird auf linke und rechte Seite entgegengesetzt addiert.
        # Dadurch faehrt eine Seite schneller und die andere langsamer.
        left_speed = self.config.base_speed + correction
        right_speed = self.config.base_speed - correction

        # Motor-Trimmung anwenden, falls eine Fahrzeugseite staerker ist.
        left_speed = left_speed * self.config.left_trim
        right_speed = right_speed * self.config.right_trim

        # Beide Geschwindigkeiten auf den erlaubten Bereich begrenzen.
        left_speed = MotorController._limit_speed(
            left_speed,
            -self.config.max_speed,
            self.config.max_speed,
        )
        right_speed = MotorController._limit_speed(
            right_speed,
            -self.config.max_speed,
            self.config.max_speed,
        )

        # Debug-Ausgabe der wichtigsten Reglerwerte.
        # Wird sichtbar, wenn logging.basicConfig(level=logging.DEBUG) gesetzt ist.
        log.debug(
            "error=%.2f correction=%.2f left=%.1f right=%.1f",
            error,
            correction,
            left_speed,
            right_speed,
        )

        # Berechnete Geschwindigkeiten an die Motorsteuerung senden.
        self.motors.drive(left_speed, right_speed)

        # Fehler fuer den naechsten D-Anteil speichern.
        self.last_error = error

    def _search_line(self):
        # Wenn keine Linie erkannt wird, dreht sich das Fahrzeug langsam.
        # Die Drehrichtung richtet sich nach der zuletzt erkannten Linienseite.
        search_direction = -1 if self.last_line_error < 0 else 1

        # Linke und rechte Seite entgegengesetzt ansteuern, damit das Fahrzeug
        # auf der Stelle bzw. sehr eng dreht.
        left_speed = search_direction * self.config.search_speed
        right_speed = -search_direction * self.config.search_speed
        self.motors.drive(left_speed, right_speed)


def main():
    # I2C-Bus des Raspberry Pi oeffnen.
    i2c = board.I2C()

    # PCA9685-PWM-Modul ueber I2C initialisieren.
    pca = PCA9685(i2c)

    # Motorsteuerung, Sensoren und Konfiguration erstellen.
    motors = MotorController(pca)
    sensors = LineSensors()
    config = LineFollowerConfig()

    # PWM-Modul vorbereiten und Motoren stoppen.
    motors.init()

    # Linienfolger erstellen und dauerhaft starten.
    follower = LineFollower(motors, sensors, config)
    follower.follow_forever()


if __name__ == "__main__":
    # main() wird nur ausgefuehrt, wenn diese Datei direkt gestartet wird.
    main()
