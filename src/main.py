import logging

import board
from adafruit_pca9685 import PCA9685

from control import Linienfolger, LinienfolgerKonfiguration
from motors import MotorSteuerung
from sensors import LinienSensoren


# Grundeinstellung fuer die Log-Ausgabe.
# INFO zeigt wichtige Start-/Stopp-Meldungen an.
# Fuer genauere Reglerwerte kann level=logging.DEBUG verwendet werden.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


def starten():
    # Einstiegspunkt des Programms.
    # Hier werden Hardware, Motorsteuerung, Sensoren und Linienfolger erzeugt.

    # I2C-Bus des Raspberry Pi oeffnen.
    i2c = board.I2C()

    # PCA9685-PWM-Modul ueber I2C initialisieren.
    pca = PCA9685(i2c)

    # Konfiguration erstellen.
    konfiguration = LinienfolgerKonfiguration()

    # Motorsteuerung und Sensoren erstellen.
    motoren = MotorSteuerung(pca, konfiguration.mindest_motor_geschwindigkeit)
    sensoren = LinienSensoren()

    # PWM-Modul vorbereiten und Motoren stoppen.
    motoren.initialisieren()

    # Linienfolger erstellen und dauerhaft starten.
    linienfolger = Linienfolger(motoren, sensoren, konfiguration)
    linienfolger.dauerhaft_folgen()


if __name__ == "__main__":
    # starten() wird nur ausgefuehrt, wenn diese Datei direkt gestartet wird.
    starten()
