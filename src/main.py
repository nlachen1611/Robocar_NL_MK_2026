import board
from adafruit_pca9685 import PCA9685

from control import LinienFolger, LinienRegler
from konfiguration import LinienfolgerKonfiguration
from motors import MotorSteuerung
from sensors import LinienSensoren


def starten():
    konfiguration = LinienfolgerKonfiguration()
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
