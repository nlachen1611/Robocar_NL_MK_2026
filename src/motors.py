from dataclasses import dataclass


PWM_FREQUENZ_HZ = 100
MAXIMALER_PWM_WERT = 0xFFFF
MINIMALE_GESCHWINDIGKEIT = -100.0
MAXIMALE_GESCHWINDIGKEIT = 100.0

KANAELE_VORNE_LINKS = (0, 1)
KANAELE_HINTEN_LINKS = (2, 3)
KANAELE_HINTEN_RECHTS = (4, 5)
KANAELE_VORNE_RECHTS = (6, 7)


@dataclass(frozen=True)
class Fahrbefehl:
    links: float
    rechts: float


class MotorSteuerung:
    def __init__(self, pwm_modul):
        self.pwm_modul = pwm_modul

    def initialisieren(self):
        self.pwm_modul.frequency = PWM_FREQUENZ_HZ
        self.stoppen()

    def stoppen(self):
        for kanal in range(8):
            self.pwm_modul.channels[kanal].duty_cycle = 0

    def ausfuehren(self, fahrbefehl):
        # Die Vorzeichen gleichen die Einbaurichtung der Motoren aus.
        self._setze_motor(KANAELE_VORNE_LINKS, fahrbefehl.links)
        self._setze_motor(KANAELE_HINTEN_LINKS, -fahrbefehl.links)
        self._setze_motor(KANAELE_VORNE_RECHTS, -fahrbefehl.rechts)
        self._setze_motor(KANAELE_HINTEN_RECHTS, fahrbefehl.rechts)

    def _setze_motor(self, kanaele, geschwindigkeit):
        kanal_a, kanal_b = kanaele
        pwm_wert = self._berechne_pwm_wert(geschwindigkeit)
        pwm_a, pwm_b = self._bestimme_pwm_richtung(geschwindigkeit, pwm_wert)
        self.pwm_modul.channels[kanal_a].duty_cycle = pwm_a
        self.pwm_modul.channels[kanal_b].duty_cycle = pwm_b

    @staticmethod
    def _berechne_pwm_wert(geschwindigkeit):
        begrenzte_geschwindigkeit = MotorSteuerung.begrenze_geschwindigkeit(
            geschwindigkeit,
        )
        return int(abs(begrenzte_geschwindigkeit) * MAXIMALER_PWM_WERT / 100)

    @staticmethod
    def _bestimme_pwm_richtung(geschwindigkeit, pwm_wert):
        if geschwindigkeit >= 0:
            return 0, pwm_wert
        return pwm_wert, 0

    @staticmethod
    def begrenze_geschwindigkeit(geschwindigkeit):
        return max(
            MINIMALE_GESCHWINDIGKEIT,
            min(MAXIMALE_GESCHWINDIGKEIT, geschwindigkeit),
        )
