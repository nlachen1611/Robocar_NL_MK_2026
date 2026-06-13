import logging
import signal
import time

from motors import MotorSteuerung

log = logging.getLogger(__name__)


class LinienfolgerKonfiguration:
    # Diese Klasse enthaelt alle Einstellwerte fuer den Linienfolger.
    # Sie ist bewusst ohne @dataclass und ohne moderne Variablen-Typangaben
    # geschrieben, damit sie auch auf aelteren Raspberry-Pi-Python-Versionen
    # stabil laeuft.
    def __init__(self):
        # Grundgeschwindigkeit, mit der das Fahrzeug geradeaus faehrt.
        # Dieser Wert wird fuer beide Fahrzeugseiten benutzt, solange keine
        # Lenk-Korrektur noetig ist.
        self.basis_geschwindigkeit = 30.0

        # Maximale erlaubte Motorgeschwindigkeit.
        # Dadurch kann die Regelung die Motoren nicht zu stark ansteuern.
        # Auch bei grosser Korrektur wird kein Motor ueber diesen Wert gesetzt.
        self.maximale_geschwindigkeit = 100.0

        # Minimale Motoransteuerung, sobald ein Motor fahren soll.
        # 0 bleibt weiterhin Stopp. Jeder andere Wert wird mindestens auf
        # diesen Betrag angehoben, damit die Motoren genug Kraft haben.
        self.mindest_motor_geschwindigkeit = 20.0

        # P-Anteil der Regelung.
        # Der Fehler wird in cm berechnet. kp gibt also an, wie stark pro cm
        # Linienabweichung gegengelenkt wird.
        # Groesserer Wert: Auto lenkt staerker.
        # Kleinerer Wert: Auto faehrt ruhiger, reagiert aber spaeter.
        self.kp = 2.0

        # D-Anteil der Regelung.
        # Dieser Anteil reagiert auf schnelle Aenderungen des geglaetteten
        # Fehlers. Zu viel kd kann bei digitalen Sensoren wieder Unruhe bringen.
        # Groesserer Wert: schnelle Richtungswechsel werden staerker bedaempft.
        # Kleinerer Wert: Auto reagiert direkter, kann aber eher pendeln.
        self.kd = 0.08

        # I-Anteil der PID-Regelung.
        # Dieser Anteil korrigiert dauerhafte kleine Abweichungen, z. B. wenn
        # eine Motorseite etwas staerker ist oder das Fahrzeug mechanisch zieht.
        # Der Wert muss klein bleiben, weil digitale Sensoren sonst schnell
        # ein Aufschaukeln verursachen koennen.
        self.ki = 0.35

        # Maximale Groesse des aufsummierten I-Fehlers.
        # Das ist der Anti-Windup-Schutz: Der I-Anteil darf sich nicht endlos
        # aufladen, wenn das Fahrzeug die Linie nicht sauber trifft.
        self.maximaler_integral_fehler = 6.0

        # Abbau-Faktor fuer den I-Anteil, wenn die Linie mittig erkannt wird.
        # 0.0 wuerde den I-Anteil sofort loeschen, 1.0 wuerde ihn nie abbauen.
        self.integral_abbau_mittig = 0.65

        # Gewichtung der geometrischen Vorsteuerung.
        # Diese nutzt Sensorabstand, Sensorposition vor den Reifen und Radbreite,
        # damit die Kurvenbewegung besser zum Fahrzeug passt.
        self.geometrie_faktor = 0.8

        # Maximale Lenk-Korrektur in Prozentpunkten.
        # Dadurch kann der Regler auf der Geraden keine extremen Spruenge machen.
        # Beispiel: basis_geschwindigkeit 20 und korrektur 5 ergibt links 25,
        # rechts 15.
        self.maximale_korrektur = 18.0

        # Geschwindigkeit der Aussenraeder in engen Kurven.
        # Dieser Wert wird benutzt, wenn nur der linke oder nur der rechte
        # Sensor die Linie sieht. Dann reicht normales Abbremsen der Innenraeder
        # oft nicht mehr aus.
        self.scharfkurve_aussen_geschwindigkeit = 40.0

        # Rueckwaertsgeschwindigkeit der Innenraeder in engen Kurven.
        # Dadurch dreht das Auto deutlich staerker in die Kurve hinein.
        self.scharfkurve_innen_rueckwaerts_geschwindigkeit = 25.0

        # Maximale Aenderung der Lenk-Korrektur pro Schleifendurchlauf.
        # Kleine Werte machen das Fahren weicher, grosse Werte reagieren schneller.
        # Dieser Wert wirkt wie eine Rampe fuer die Lenkung.
        self.maximaler_korrektur_schritt = 2.0

        # Fehlerbereich um die Mitte, in dem nicht gelenkt wird.
        # Das verhindert Hin-und-her-Pendeln, wenn der mittlere Sensor die Linie
        # sauber trifft.
        # Bei digitalen Sensoren ist diese Totzone wichtig, weil die Messwerte
        # sonst sofort zwischen links, mitte und rechts springen koennen.
        self.totzone_cm = 0.5

        # Glaettung des Linienfehlers.
        # 0.0 = sehr traege, 1.0 = keine Glaettung.
        # 0.25 bedeutet: 25 Prozent neuer Messwert, 75 Prozent alter Wert.
        self.fehler_filter_alpha = 0.25

        # Abstand zwischen zwei benachbarten Sensoren in cm.
        # Links liegt dadurch bei -1.5 cm, Mitte bei 0 cm, rechts bei +1.5 cm.
        self.sensor_abstand_cm = 1.5

        # Abstand der Sensorreihe vor den Reifen in cm.
        # Dieser Wert wird dokumentiert und kann spaeter fuer Kurvenmodelle
        # genutzt werden. Bei digitalen Sensoren hilft vor allem die Sensorbreite.
        # Die Sensoren sitzen 1.5 cm vor den Reifen und erkennen die Linie somit
        # etwas frueher als die Raeder sie erreichen.
        self.sensor_vorstand_cm = 1.5

        # Reifendurchmesser in cm.
        # Der Wert ist hier abgelegt, damit die Fahrzeug-Geometrie vollstaendig
        # im Programm dokumentiert ist.
        self.reifen_durchmesser_cm = 6.5

        # Radabstand vorne-hinten in cm.
        # Das ist der Abstand zwischen vorderem und hinterem Rad.
        self.radstand_cm = 9.5

        # Innenabstand zwischen linkem und rechtem Rad in cm.
        # Das ist der Abstand von der Innenseite eines Rads bis zur Innenseite
        # des anderen Rads.
        self.rad_innenabstand_cm = 10.5

        # Abstand von Radmitte links zu Radmitte rechts in cm.
        # Innenabstand + Reifendurchmesser ergibt naeherungsweise die Spurweite
        # zwischen den Radmittelpunkten.
        self.spurweite_cm = self.rad_innenabstand_cm + self.reifen_durchmesser_cm

        # Wirksamer Blickabstand fuer die Linienregelung.
        # Die Sensoren sitzen vor den Reifen. Zusammen mit etwa halbem Radstand
        # ergibt das einen stabileren geometrischen Bezugspunkt.
        self.blickabstand_cm = self.sensor_vorstand_cm + (self.radstand_cm / 2.0)

        # Einzelrad-Feineinstellung fuer ungleich starke Motoren.
        # Werte ueber 1.0 machen das Rad staerker, Werte unter 1.0 schwaecher.
        # Beispiel: trim_vorne_links = 0.95 macht das vordere linke Rad
        # 5 Prozent langsamer.
        self.trim_vorne_links = 1.0
        self.trim_hinten_links = 1.0
        self.trim_vorne_rechts = 1.0
        self.trim_hinten_rechts = 1.0

        # Pause zwischen zwei Regelungsdurchlaeufen in Sekunden.
        # 0.03 Sekunden entsprechen etwa 33 Messungen pro Sekunde.
        self.schleifen_pause = 0.03

        # Geschwindigkeit, mit der sich das Fahrzeug dreht, wenn keine Linie
        # erkannt wird.
        self.such_geschwindigkeit = 22.0

        # Wert, den die Liniensensoren liefern, wenn sie schwarz erkennen.
        # Falls die Sensoren umgekehrt arbeiten, muss dieser Wert auf 0
        # gesetzt werden.
        self.schwarz_wert = 1


class Linienfolger:
    # Diese Klasse enthaelt die eigentliche Linienfolger-Regelung.
    def __init__(self, motoren, sensoren, konfiguration):
        # Motorsteuerung, Sensoren und Einstellwerte speichern.
        self.motoren = motoren
        self.sensoren = sensoren
        self.konfiguration = konfiguration

        # Letzter Regelfehler fuer den D-Anteil der Regelung.
        # Dieser Wert wird benoetigt, um zu erkennen, wie schnell sich die
        # Linienabweichung veraendert.
        self.letzter_fehler = 0.0

        # Geglaetteter Linienfehler in cm.
        # Dieser Wert verhindert, dass einzelne Sensorwechsel sofort zu einer
        # harten Motorreaktion fuehren.
        self.gefilterter_fehler = 0.0

        # Letzte Lenk-Korrektur. Damit werden ploetzliche Spruenge begrenzt.
        self.letzte_korrektur = 0.0

        # Aufsummierter Fehler fuer den I-Anteil der PID-Regelung.
        self.integral_fehler = 0.0

        # Zeitpunkt des letzten Regelungsdurchlaufs.
        # Daraus wird die echte Zeitdifferenz fuer I- und D-Anteil berechnet.
        self.letzte_regelzeit = time.monotonic()

        # Letzte bekannte Linienrichtung.
        # Diese wird verwendet, wenn die Linie kurz verloren geht.
        self.letzter_linien_fehler = 0.0

        # Laufvariable fuer die Hauptschleife.
        self.laeuft = True

    def stoppen(self, *_):
        # Wird bei Strg+C oder beim Beenden des Programms aufgerufen.
        self.laeuft = False

    def dauerhaft_folgen(self):
        # Signalhandler registrieren, damit die Motoren beim Beenden
        # sauber ausgeschaltet werden.
        # SIGINT entsteht z. B. bei Strg+C.
        signal.signal(signal.SIGINT, self.stoppen)

        # SIGTERM entsteht, wenn das Programm von aussen beendet wird.
        signal.signal(signal.SIGTERM, self.stoppen)

        log.info("start line follower")
        try:
            # Hauptschleife: Sensoren lesen, Fehler berechnen, Motoren ansteuern.
            while self.laeuft:
                # Sensoren als Schwarz-Erkennung lesen.
                # Das Ergebnis ist ein Tupel wie z. B. (0, 1, 0).
                sensor_werte = self.sensoren.schwarz_lesen(
                    self.konfiguration.schwarz_wert,
                )

                # Aus den Sensorwerten wird ein Linienfehler berechnet.
                # Der Fehler wird in cm angegeben:
                # negativ = Linie links, positiv = Linie rechts.
                fehler = self._linien_fehler_berechnen(sensor_werte)

                if fehler is None:
                    # Keine Linie erkannt: Fahrzeug sucht die Linie wieder.
                    self._pid_speicher_zuruecksetzen()
                    self._linie_suchen()
                else:
                    # Linie erkannt: normale Regelung ausfuehren.
                    self._linie_folgen(fehler, sensor_werte)

                # Kurze Pause, damit die Schleife kontrolliert laeuft.
                time.sleep(self.konfiguration.schleifen_pause)
        finally:
            # Dieser Block wird auch bei Fehlern oder Strg+C ausgefuehrt.
            # Dadurch bleiben die Motoren nicht unbeabsichtigt eingeschaltet.
            log.info("stop motors")
            self.motoren.alle_stoppen()

    def _linien_fehler_berechnen(self, werte):
        # Diese Methode rechnet die drei digitalen Sensoren in einen
        # geometrischen Linienfehler um.
        #
        # Rueckgabe:
        # - negative Zahl: Linie liegt links der Mitte
        # - 0.0: Linie liegt mittig
        # - positive Zahl: Linie liegt rechts der Mitte
        # - None: keine Linie erkannt

        # Sensorwerte auf einzelne Namen aufteilen.
        links, mitte, rechts = werte

        # Anzahl der Sensoren, die gerade schwarz erkennen.
        aktive_sensoren = links + mitte + rechts

        if aktive_sensoren == 0:
            # Kein Sensor sieht die Linie.
            # Die Regelung kann dann keinen exakten Fehler berechnen.
            return None

        # Gewichtete Fehlerberechnung in cm:
        # links  = -Sensorabstand
        # mitte  =  0 cm
        # rechts = +Sensorabstand
        sensor_abstand = self.konfiguration.sensor_abstand_cm

        # Wenn mehrere Sensoren gleichzeitig schwarz sehen, wird der Mittelwert
        # gebildet. Dadurch entsteht z. B. bei links+mitte der Wert -0.75 cm
        # statt direkt -1.5 cm. Das macht Kurvenuebergaenge weicher.
        fehler = (
            (-sensor_abstand * links) + (0.0 * mitte) + (sensor_abstand * rechts)
        ) / aktive_sensoren

        # Letzte bekannte Linienposition speichern.
        self.letzter_linien_fehler = fehler
        return fehler

    def _linie_folgen(self, roher_fehler, sensor_werte):
        # Diese Methode berechnet aus dem Linienfehler die vier
        # Motor-Geschwindigkeiten.

        # Der rohe Sensorfehler springt bei digitalen Sensoren hart zwischen
        # wenigen Werten. Deshalb wird er geglaettet.
        alpha = self.konfiguration.fehler_filter_alpha
        self.gefilterter_fehler = (alpha * roher_fehler) + (
            (1.0 - alpha) * self.gefilterter_fehler
        )

        # Wenn die Linie genau mittig erkannt wird, wird der geglaettete Fehler
        # aktiv in Richtung 0 gezogen. Das verbessert besonders die Geradeausfahrt.
        linie_ist_mittig = roher_fehler == 0
        if linie_ist_mittig:
            self.gefilterter_fehler = 0.0

        # Ab hier wird mit dem geglaetteten Fehler weitergerechnet.
        fehler = self.gefilterter_fehler

        # Kleine Fehler um die Mitte werden ignoriert. Sonst pendelt das Auto
        # wegen Sensorrauschen staendig links-rechts.
        if abs(fehler) < self.konfiguration.totzone_cm:
            fehler = 0.0

        # Echte Zeitdifferenz seit dem letzten Regelungsdurchlauf berechnen.
        # Dadurch arbeitet I und D auch dann korrekt, wenn die Schleife leicht
        # schwankt.
        aktuelle_zeit = time.monotonic()
        zeit_delta = aktuelle_zeit - self.letzte_regelzeit
        self.letzte_regelzeit = aktuelle_zeit

        if zeit_delta <= 0:
            zeit_delta = self.konfiguration.schleifen_pause

        # Aenderung des Fehlers pro Sekunde.
        # Dieser Wert bildet den D-Anteil.
        fehler_aenderung = (fehler - self.letzter_fehler) / zeit_delta

        if fehler == 0:
            # Wenn kein nutzbarer Fehler vorhanden ist, soll auch der D-Anteil
            # keine alte Gegenbewegung erzeugen.
            fehler_aenderung = 0.0

        # I-Anteil berechnen.
        # Nur kleine bis mittlere Fehler werden aufsummiert. Bei scharfen Kurven
        # oder starkem Linienversatz soll der I-Anteil nicht weiter aufladen,
        # weil dort P/D und Scharfkurvenmodus wichtiger sind.
        if fehler == 0:
            self.integral_fehler = (
                self.integral_fehler * self.konfiguration.integral_abbau_mittig
            )
        elif abs(fehler) <= self.konfiguration.sensor_abstand_cm:
            self.integral_fehler = self.integral_fehler + (fehler * zeit_delta)
            self.integral_fehler = MotorSteuerung.geschwindigkeit_begrenzen(
                self.integral_fehler,
                -self.konfiguration.maximaler_integral_fehler,
                self.konfiguration.maximaler_integral_fehler,
            )

        # Geometrische Vorsteuerung:
        # Der Fehler am Sensor wird mit dem Blickabstand in eine ungefaehre
        # Kruemmung umgerechnet. Daraus entsteht ein Geschwindigkeitsunterschied
        # zwischen linker und rechter Seite, passend zur Spurweite des Fahrzeugs.
        geometrie_korrektur = self._geometrische_korrektur_berechnen(fehler)

        # PID-Regler:
        # P-Anteil: aktueller geglaetteter Fehler in cm
        # I-Anteil: aufsummierter Fehler ueber die Zeit
        # D-Anteil: Aenderung des geglaetteten Fehlers
        # Das Ergebnis ist die Lenk-Korrektur.
        ziel_korrektur = (
            (self.konfiguration.kp * fehler)
            + (self.konfiguration.ki * self.integral_fehler)
            + (self.konfiguration.kd * fehler_aenderung)
            + geometrie_korrektur
        )

        # Die Ziel-Korrektur wird begrenzt, damit der Regler nicht zu aggressiv
        # wird. Gerade bei digitalen Sensoren verhindert das starke Schlenker.
        ziel_korrektur = MotorSteuerung.geschwindigkeit_begrenzen(
            ziel_korrektur,
            -self.konfiguration.maximale_korrektur,
            self.konfiguration.maximale_korrektur,
        )

        if linie_ist_mittig:
            # Auf der Geraden keine alte Korrektur auslaufen lassen.
            # Beide Fahrzeugseiten bekommen dadurch sofort dieselbe Vorgabe.
            korrektur = MotorSteuerung.geschwindigkeit_begrenzen(
                self.konfiguration.ki * self.integral_fehler,
                -2.0,
                2.0,
            )
        else:
            # Korrektur weich begrenzen, damit die Motorwerte nicht sprunghaft
            # wechseln. Das ist einer der wichtigsten Punkte gegen Pendeln.
            korrektur_schritt = ziel_korrektur - self.letzte_korrektur
            korrektur_schritt = MotorSteuerung.geschwindigkeit_begrenzen(
                korrektur_schritt,
                -self.konfiguration.maximaler_korrektur_schritt,
                self.konfiguration.maximaler_korrektur_schritt,
            )
            korrektur = self.letzte_korrektur + korrektur_schritt

        # Die Korrektur wird auf linke und rechte Seite entgegengesetzt addiert.
        # Dadurch faehrt eine Seite schneller und die andere langsamer.
        linke_geschwindigkeit = self.konfiguration.basis_geschwindigkeit + korrektur
        rechte_geschwindigkeit = self.konfiguration.basis_geschwindigkeit - korrektur

        # Scharfkurven-Modus:
        # Wenn nur der linke oder nur der rechte Sensor schwarz sieht, ist die
        # Linie weit aussen. Dann werden die Innenraeder bewusst rueckwaerts
        # angesteuert und die Aussenraeder kraeftig vorwaerts.
        linker_sensor, mittlerer_sensor, rechter_sensor = sensor_werte
        nur_linker_sensor = (
            linker_sensor == 1 and mittlerer_sensor == 0 and rechter_sensor == 0
        )
        nur_rechter_sensor = (
            linker_sensor == 0 and mittlerer_sensor == 0 and rechter_sensor == 1
        )

        if nur_linker_sensor:
            # Linie liegt deutlich links:
            # linke Innenraeder rueckwaerts, rechte Aussenraeder vorwaerts.
            self._pid_speicher_zuruecksetzen()
            linke_geschwindigkeit = (
                -self.konfiguration.scharfkurve_innen_rueckwaerts_geschwindigkeit
            )
            rechte_geschwindigkeit = (
                self.konfiguration.scharfkurve_aussen_geschwindigkeit
            )
        elif nur_rechter_sensor:
            # Linie liegt deutlich rechts:
            # rechte Innenraeder rueckwaerts, linke Aussenraeder vorwaerts.
            self._pid_speicher_zuruecksetzen()
            linke_geschwindigkeit = (
                self.konfiguration.scharfkurve_aussen_geschwindigkeit
            )
            rechte_geschwindigkeit = (
                -self.konfiguration.scharfkurve_innen_rueckwaerts_geschwindigkeit
            )

        # Einzelrad-Trimmung anwenden, falls einzelne Motoren unterschiedlich
        # stark sind. Das ist genauer als nur eine linke/rechte Trimmung.
        vorne_links_geschwindigkeit = (
            linke_geschwindigkeit * self.konfiguration.trim_vorne_links
        )
        hinten_links_geschwindigkeit = (
            linke_geschwindigkeit * self.konfiguration.trim_hinten_links
        )
        vorne_rechts_geschwindigkeit = (
            rechte_geschwindigkeit * self.konfiguration.trim_vorne_rechts
        )
        hinten_rechts_geschwindigkeit = (
            rechte_geschwindigkeit * self.konfiguration.trim_hinten_rechts
        )

        # Alle vier Geschwindigkeiten auf den erlaubten Bereich begrenzen.
        vorne_links_geschwindigkeit = MotorSteuerung.geschwindigkeit_begrenzen(
            vorne_links_geschwindigkeit,
            -self.konfiguration.maximale_geschwindigkeit,
            self.konfiguration.maximale_geschwindigkeit,
        )
        hinten_links_geschwindigkeit = MotorSteuerung.geschwindigkeit_begrenzen(
            hinten_links_geschwindigkeit,
            -self.konfiguration.maximale_geschwindigkeit,
            self.konfiguration.maximale_geschwindigkeit,
        )
        vorne_rechts_geschwindigkeit = MotorSteuerung.geschwindigkeit_begrenzen(
            vorne_rechts_geschwindigkeit,
            -self.konfiguration.maximale_geschwindigkeit,
            self.konfiguration.maximale_geschwindigkeit,
        )
        hinten_rechts_geschwindigkeit = MotorSteuerung.geschwindigkeit_begrenzen(
            hinten_rechts_geschwindigkeit,
            -self.konfiguration.maximale_geschwindigkeit,
            self.konfiguration.maximale_geschwindigkeit,
        )

        # Debug-Ausgabe der wichtigsten Reglerwerte.
        # Wird sichtbar, wenn logging.basicConfig(level=logging.DEBUG) gesetzt ist.
        log.debug(
            "roh=%.2f gefiltert=%.2f integral=%.2f korrektur=%.2f vl=%.1f hl=%.1f vr=%.1f hr=%.1f",
            roher_fehler,
            fehler,
            self.integral_fehler,
            korrektur,
            vorne_links_geschwindigkeit,
            hinten_links_geschwindigkeit,
            vorne_rechts_geschwindigkeit,
            hinten_rechts_geschwindigkeit,
        )

        # Berechnete Geschwindigkeiten an die Motorsteuerung senden.
        self.motoren.raeder_fahren(
            vorne_links_geschwindigkeit,
            hinten_links_geschwindigkeit,
            vorne_rechts_geschwindigkeit,
            hinten_rechts_geschwindigkeit,
        )

        # Fehler fuer den naechsten D-Anteil speichern.
        self.letzter_fehler = fehler
        self.letzte_korrektur = korrektur

    def _geometrische_korrektur_berechnen(self, fehler):
        # Diese Vorsteuerung nutzt die Fahrzeugmasse:
        # - Sensorabstand und Fehler sagen, wie weit die Linie seitlich liegt.
        # - Blickabstand sagt, wie weit vor dem Fahrzeug gemessen wird.
        # - Spurweite sagt, wie stark linke/rechte Seite unterschiedlich laufen
        #   muessen, um eine Kurve einzuleiten.
        #
        # Bei Fehler 0 ergibt sich auch Korrektur 0.
        if fehler == 0:
            return 0.0

        blickabstand = max(1.0, self.konfiguration.blickabstand_cm)
        spurweite = max(1.0, self.konfiguration.spurweite_cm)

        # Vereinfachte Pure-Pursuit-Kruemmung:
        # Je groesser der seitliche Fehler und je kleiner der Blickabstand,
        # desto staerker soll eingelenkt werden.
        kruemmung = (2.0 * fehler) / ((blickabstand * blickabstand) + (fehler * fehler))

        # Aus der Kruemmung wird ein Geschwindigkeitsunterschied abgeleitet.
        korrektur = (
            self.konfiguration.basis_geschwindigkeit
            * spurweite
            * kruemmung
            * self.konfiguration.geometrie_faktor
        )

        return MotorSteuerung.geschwindigkeit_begrenzen(
            korrektur,
            -self.konfiguration.maximale_korrektur,
            self.konfiguration.maximale_korrektur,
        )

    def _pid_speicher_zuruecksetzen(self):
        # Bei Linienverlust oder Scharfkurvenmodus wird der PID-Speicher
        # zurueckgesetzt. Sonst koennte der I-Anteil nach der Kurve noch eine
        # alte Korrektur erzwingen.
        self.integral_fehler = 0.0
        self.letzter_fehler = 0.0
        self.letzte_korrektur = 0.0
        self.gefilterter_fehler = 0.0
        self.letzte_regelzeit = time.monotonic()

    def _linie_suchen(self):
        # Wenn keine Linie erkannt wird, dreht sich das Fahrzeug langsam.
        # Die Drehrichtung richtet sich nach der zuletzt erkannten Linienseite.
        such_richtung = -1 if self.letzter_linien_fehler < 0 else 1

        # Linke und rechte Seite entgegengesetzt ansteuern, damit das Fahrzeug
        # auf der Stelle bzw. sehr eng dreht.
        linke_geschwindigkeit = such_richtung * self.konfiguration.such_geschwindigkeit
        rechte_geschwindigkeit = (
            -such_richtung * self.konfiguration.such_geschwindigkeit
        )
        self.motoren.fahren(linke_geschwindigkeit, rechte_geschwindigkeit)
