import signal
import time

from motors import Fahrbefehl, MotorSteuerung


LINIE_LINKS = -1.0
LINIE_MITTE = 0.0
LINIE_RECHTS = 1.0


class LinienRegler:
    def __init__(self, konfiguration):
        self.konfiguration = konfiguration
        self.letzter_fehler = LINIE_MITTE
        self.letzte_linienposition = LINIE_MITTE

    def berechne_fahrbefehl(self, sensor_werte):
        linienfehler = self._berechne_linienfehler(sensor_werte)

        if linienfehler is None:
            return self._berechne_suchbefehl()

        return self._berechne_folgebefehl(linienfehler)

    @staticmethod
    def _berechne_linienfehler(sensor_werte):
        aktive_sensoren = sensor_werte.anzahl_aktiver_sensoren()

        if aktive_sensoren == 0:
            return None

        gewichtete_position = (
            LINIE_LINKS * sensor_werte.links
            + LINIE_MITTE * sensor_werte.mitte
            + LINIE_RECHTS * sensor_werte.rechts
        )
        return gewichtete_position / aktive_sensoren

    def _berechne_folgebefehl(self, linienfehler):
        korrektur = self._berechne_korrektur(linienfehler)
        self.letzter_fehler = linienfehler
        self.letzte_linienposition = linienfehler
        return self._erstelle_fahrbefehl(korrektur)

    def _berechne_korrektur(self, linienfehler):
        if linienfehler == LINIE_MITTE:
            return 0.0

        fehler_aenderung = linienfehler - self.letzter_fehler
        return (
            self.konfiguration.p_faktor * linienfehler
            + self.konfiguration.d_faktor * fehler_aenderung
        )

    def _erstelle_fahrbefehl(self, korrektur):
        links = self.konfiguration.basis_geschwindigkeit + korrektur
        rechts = self.konfiguration.basis_geschwindigkeit - korrektur
        return Fahrbefehl(
            links=self._begrenze_und_trimme(links, self.konfiguration.trim_links),
            rechts=self._begrenze_und_trimme(rechts, self.konfiguration.trim_rechts),
        )

    def _begrenze_und_trimme(self, geschwindigkeit, trim):
        getrimmte_geschwindigkeit = geschwindigkeit * trim
        maximale_geschwindigkeit = self.konfiguration.maximale_geschwindigkeit
        return max(
            -maximale_geschwindigkeit,
            min(maximale_geschwindigkeit, getrimmte_geschwindigkeit),
        )

    def _berechne_suchbefehl(self):
        suchrichtung = -1 if self.letzte_linienposition < LINIE_MITTE else 1
        such_geschwindigkeit = self.konfiguration.such_geschwindigkeit
        return Fahrbefehl(
            links=suchrichtung * such_geschwindigkeit,
            rechts=-suchrichtung * such_geschwindigkeit,
        )


class LinienFolger:
    def __init__(self, motor_steuerung, linien_sensoren, linien_regler):
        self.motor_steuerung = motor_steuerung
        self.linien_sensoren = linien_sensoren
        self.linien_regler = linien_regler
        self.laeuft = True

    def starten(self):
        self._registriere_stoppsignale()

        try:
            self._regelkreis_ausfuehren()
        finally:
            self.motor_steuerung.stoppen()

    def stoppen(self, *_):
        self.laeuft = False

    def _registriere_stoppsignale(self):
        signal.signal(signal.SIGINT, self.stoppen)
        signal.signal(signal.SIGTERM, self.stoppen)

    def _regelkreis_ausfuehren(self):
        regelintervall = self.linien_regler.konfiguration.regelintervall_sekunden

        while self.laeuft:
            self._regelzyklus_ausfuehren()
            time.sleep(regelintervall)

    def _regelzyklus_ausfuehren(self):
        sensor_werte = self.linien_sensoren.schwarz_lesen()
        fahrbefehl = self.linien_regler.berechne_fahrbefehl(sensor_werte)
        self.motor_steuerung.ausfuehren(fahrbefehl)
