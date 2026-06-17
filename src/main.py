import json
import board
from adafruit_pca9685 import PCA9685
from pathlib import Path
from types import SimpleNamespace

from control import LinienFolger, LinienRegler
from motors import MotorSteuerung
from sensors import LinienSensoren


def lade_konfiguration():
    pfad = Path(__file__).with_name("config.json")
    with pfad.open(encoding="utf-8") as datei:
        daten = json.load(datei)
    return SimpleNamespace(**daten)


def starten():
    konfiguration = lade_konfiguration()
    pwm_modul = PCA9685(board.I2C())
    motor_steuerung = MotorSteuerung(pwm_modul)
    linien_sensoren = LinienSensoren(konfiguration.schwarz_wert)
    linien_regler = LinienRegler(konfiguration)
    linien_folger = LinienFolger(
        motor_steuerung,
        linien_sensoren,
        linien_regler,
    )

    motor_steuerung.initialisieren()
    linien_folger.starten()


if __name__ == "__main__":
    starten()
