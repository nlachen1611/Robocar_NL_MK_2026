# Autonomer Linienfolger mit Raspberry Pi

Dieses Projekt steuert ein vierrädriges Roboterfahrzeug, das mithilfe von drei
digitalen Infrarotsensoren einer schwarzen Linie folgt. Die Motoren werden über
einen PCA9685-PWM-Treiber angesteuert. Zur Berechnung der Lenkbewegung verwendet
das Fahrzeug eine PD-Regelung.

Der Code wurde nach grundlegenden Clean-Code-Prinzipien aufgebaut. Sensorik,
Motorsteuerung, Regelung, Konfiguration und Programmstart sind in getrennten
Modulen organisiert. Die Namen der Klassen, Funktionen und Variablen beschreiben
ihre jeweilige Aufgabe. Funktionen sind kurz gehalten und übernehmen möglichst
nur eine Verantwortung.

## Funktionsweise

Die drei Liniensensoren befinden sich mittig vor den Rädern und erkennen, ob sich
unter ihnen eine schwarze Linie befindet:

| Sensor | GPIO-Pin | Position |
|---|---:|---|
| Links | 14 | Linke Linienseite |
| Mitte | 15 | Fahrzeugmitte |
| Rechts | 23 | Rechte Linienseite |

Aus den aktiven Sensoren wird eine relative Linienposition berechnet:

| Sensorzustand `(links, mitte, rechts)` | Linienfehler | Bedeutung |
|---|---:|---|
| `(1, 0, 0)` | `-1,0` | Linie liegt links |
| `(1, 1, 0)` | `-0,5` | Linie liegt leicht links |
| `(0, 1, 0)` | `0,0` | Linie liegt mittig |
| `(0, 1, 1)` | `+0,5` | Linie liegt leicht rechts |
| `(0, 0, 1)` | `+1,0` | Linie liegt rechts |
| `(0, 0, 0)` | Keine Position | Linie wurde verloren |

Wenn die Linie erkannt wird, berechnet die PD-Regelung einen Korrekturwert:

```text
Korrektur = P-Faktor × Linienfehler
           + D-Faktor × Fehleränderung
```

Der P-Anteil reagiert auf die aktuelle Abweichung von der Linie. Der D-Anteil
reagiert auf die Änderung des Fehlers und verstärkt die Reaktion beim Übergang
in eine Kurve.

Aus dem Korrekturwert entstehen die Geschwindigkeiten der beiden
Fahrzeugseiten:

```text
Linke Geschwindigkeit  = Basisgeschwindigkeit + Korrektur
Rechte Geschwindigkeit = Basisgeschwindigkeit - Korrektur
```

Wenn keine Linie erkannt wird, dreht das Fahrzeug in die zuletzt bekannte
Linienrichtung, um die Linie wiederzufinden.

## Hardware

Für das Projekt werden folgende Komponenten benötigt:

- Raspberry Pi mit aktiviertem I2C
- PCA9685-PWM-Treiber
- Motortreiber beziehungsweise Motoransteuerung passend zum Fahrzeug
- Vier Gleichstrommotoren
- Drei digitale Infrarot-Liniensensoren
- Geeignete Spannungsversorgung für Raspberry Pi und Motoren
- Schwarze Fahrbahnlinie auf hellem Untergrund

Die verwendete Fahrzeuggeometrie:

| Eigenschaft | Wert |
|---|---:|
| Reifendurchmesser | 6,5 cm |
| Radabstand vorne zu hinten | 9,5 cm |
| Innenabstand zwischen linker und rechter Radseite | 10,5 cm |
| Abstand zwischen zwei Sensoren | 1,5 cm |
| Sensorposition vor den Reifen | 1,5 cm |
| Linienbreite | 1,5 cm |

## Motorbelegung

Jeder Motor verwendet zwei Kanäle des PCA9685. Dadurch kann die Drehrichtung
über zwei PWM-Ausgänge gesteuert werden.

| Motor | PCA9685-Kanäle |
|---|---|
| Vorne links | 0 und 1 |
| Hinten links | 2 und 3 |
| Hinten rechts | 4 und 5 |
| Vorne rechts | 6 und 7 |

Die PWM-Frequenz beträgt `100 Hz`. Die Geschwindigkeit wird als Prozentwert
zwischen `-100` und `+100` angegeben:

- Positive Werte: Fahrt in Vorwärtsrichtung
- Negative Werte: Fahrt in Rückwärtsrichtung
- `0`: Motor steht

Die Vorzeichen einzelner Motoren werden in `motors.py` umgedreht, weil die
Motoren aufgrund ihrer Einbaurichtung nicht alle bei demselben Vorzeichen in
dieselbe Fahrzeugrichtung drehen.

## Projektstruktur

```text
finaler_code/
├── main.py
├── konfiguration.py
├── control.py
├── motors.py
├── sensors.py
└── README.md
```

### `main.py`

Erstellt die Hardware- und Softwarekomponenten, verbindet sie miteinander und
startet den Linienfolger.

### `konfiguration.py`

Enthält alle Werte, die das Fahrverhalten beeinflussen. Dadurch können
Geschwindigkeit und Regelung angepasst werden, ohne die eigentliche
Programmlogik zu verändern.

### `control.py`

Enthält die PD-Regelung und den Regelkreis. Das Modul berechnet aus den
Sensorwerten einen Fahrbefehl für die linke und rechte Fahrzeugseite.

### `motors.py`

Wandelt Fahrbefehle in PWM-Werte um und gibt sie über den PCA9685 an die vier
Motoren aus.

### `sensors.py`

Liest die drei digitalen Liniensensoren und stellt deren Zustände als
`SensorWerte` bereit.

## Installation

### 1. I2C aktivieren

Auf dem Raspberry Pi muss I2C aktiviert sein:

```bash
sudo raspi-config
```

Unter `Interface Options` die I2C-Schnittstelle aktivieren und den Raspberry Pi
anschließend neu starten.

### 2. Python-Abhängigkeiten installieren

Das Programm wird mit Python 3 ausgeführt. Die benötigten Bibliotheken können
mit `pip` installiert werden:

```bash
python3 -m pip install adafruit-circuitpython-pca9685 gpiozero
```

Je nach Raspberry-Pi-Installation können zusätzlich folgende Pakete benötigt
werden:

```bash
python3 -m pip install adafruit-blinka
```

### 3. I2C-Verbindung prüfen

Der PCA9685 sollte über I2C erkannt werden:

```bash
sudo i2cdetect -y 1
```

Bei der Standardadresse sollte in der Ausgabe normalerweise `40` erscheinen.

## Programm starten

In den Projektordner wechseln:

```bash
cd finaler_code
```

Programm starten:

```bash
python3 main.py
```

Das Programm kann mit `Strg+C` beendet werden. Beim Beenden werden alle Motoren
über einen `finally`-Block sicher gestoppt.

## Konfiguration

Die wichtigsten Fahrwerte befinden sich in `konfiguration.py`:

```python
@dataclass(frozen=True)
class LinienfolgerKonfiguration:
    basis_geschwindigkeit: float = 30.0
    maximale_geschwindigkeit: float = 100.0
    p_faktor: float = 10.0
    d_faktor: float = 15.0
    trim_links: float = 1.0
    trim_rechts: float = 1.0
    regelintervall_sekunden: float = 0.03
    such_geschwindigkeit: float = 35.0
    schwarz_wert: int = 1
```

### Basisgeschwindigkeit

```python
basis_geschwindigkeit = 30.0
```

Bestimmt die normale Geschwindigkeit des Fahrzeugs. Ein höherer Wert macht das
Fahrzeug schneller, kann aber auch das Pendeln auf geraden Strecken verstärken.

### Maximale Geschwindigkeit

```python
maximale_geschwindigkeit = 100.0
```

Begrenzt die ausgegebene Geschwindigkeit. Der Wert `100` entspricht der maximal
möglichen PWM-Ansteuerung.

### P-Faktor

```python
p_faktor = 10.0
```

Bestimmt, wie stark das Fahrzeug auf die aktuelle Linienabweichung reagiert.

- Höherer Wert: stärkere Kurvenreaktion
- Niedrigerer Wert: ruhigere Fahrt
- Zu hoher Wert: starkes Pendeln
- Zu niedriger Wert: Linie wird in Kurven verloren

### D-Faktor

```python
d_faktor = 15.0
```

Bestimmt, wie stark das Fahrzeug auf eine Änderung des Linienfehlers reagiert.

- Höherer Wert: stärkere Reaktion beim Eintritt in eine Kurve
- Niedrigerer Wert: kleinere Lenksprünge
- Zu hoher Wert: starkes Pendeln bei Sensorwechseln

### Seitentrimmung

```python
trim_links = 1.0
trim_rechts = 1.0
```

Mit der Seitentrimmung können unterschiedlich starke Motorseiten ausgeglichen
werden.

Wenn das Fahrzeug dauerhaft nach links zieht, kann beispielsweise die rechte
Seite leicht verstärkt werden:

```python
trim_rechts = 1.03
```

Wenn das Fahrzeug dauerhaft nach rechts zieht:

```python
trim_links = 1.03
```

### Suchgeschwindigkeit

```python
such_geschwindigkeit = 35.0
```

Bestimmt die Drehgeschwindigkeit, wenn kein Sensor die Linie erkennt. Ein zu
kleiner Wert kann dazu führen, dass das Fahrzeug die Linie nicht schnell genug
wiederfindet. Ein zu großer Wert kann zum Überschwingen führen.

### Schwarz-Wert

```python
schwarz_wert = 1
```

Einige Sensormodule liefern bei schwarzem Untergrund `1`, andere liefern `0`.
Wenn das Fahrzeug helle Flächen als Linie erkennt, muss dieser Wert geändert
werden:

```python
schwarz_wert = 0
```

## Beispielberechnungen

Bei einer Basisgeschwindigkeit von `30`, einem P-Faktor von `10` und einem
D-Faktor von `15` ergeben sich beispielsweise folgende Befehle.

### Geradeausfahrt

Nur der mittlere Sensor erkennt die Linie:

```text
Fehler = 0
Korrektur = 0
Links = 30
Rechts = 30
```

### Wechsel in eine Rechtskurve

Der Fehler wechselt von `0` auf `+1`:

```text
Fehleränderung = 1 - 0 = 1
Korrektur = 10 × 1 + 15 × 1 = 25
Links = 30 + 25 = 55
Rechts = 30 - 25 = 5
```

### Konstante Rechtskurve

Der rechte Sensor erkennt weiterhin die Linie:

```text
Fehler = 1
Fehleränderung = 1 - 1 = 0
Korrektur = 10 × 1 + 15 × 0 = 10
Links = 30 + 10 = 40
Rechts = 30 - 10 = 20
```

### Linie verloren

Wenn kein Sensor die Linie erkennt, dreht das Fahrzeug mit der
Suchgeschwindigkeit in die zuletzt bekannte Linienrichtung:

```text
Links = +35
Rechts = -35
```

## Abstimmung des Fahrverhaltens

Bei der Abstimmung sollte immer nur ein Wert gleichzeitig verändert werden.
Nach jeder Änderung sollte das Fahrzeug sowohl auf einer Geraden als auch in
engen und weiten Kurven getestet werden.

### Fahrzeug pendelt auf der Geraden

1. `d_faktor` schrittweise reduzieren.
2. Falls nötig `p_faktor` leicht reduzieren.
3. Prüfen, ob das Fahrzeug dauerhaft zu einer Seite zieht und eine Trimmung
   benötigt.

Beispiel:

```python
p_faktor = 8.0
d_faktor = 8.0
```

### Fahrzeug reagiert zu schwach auf Kurven

1. `p_faktor` schrittweise erhöhen.
2. Falls der Kurvenbeginn zu langsam ist, `d_faktor` leicht erhöhen.
3. Gegebenenfalls die Basisgeschwindigkeit reduzieren, damit mehr Zeit zum
   Reagieren bleibt.

### Fahrzeug findet eine verlorene Linie zu langsam

Die Suchgeschwindigkeit erhöhen:

```python
such_geschwindigkeit = 45.0
```

### Fahrzeug fährt dauerhaft schief

Die Seitentrimmung anpassen. Dabei nur kleine Schritte verwenden, zum Beispiel
`0,01` bis `0,03`.

## Sicherheitshinweise

- Das Fahrzeug beim ersten Test aufbocken, damit sich die Räder frei drehen
  können.
- Vor dem Einschalten die Motorbelegung und Drehrichtung prüfen.
- Für die Motoren eine geeignete separate Spannungsversorgung verwenden.
- Masseverbindungen der beteiligten Komponenten korrekt verbinden.
- Das Fahrzeug zunächst mit niedriger Geschwindigkeit testen.
- Sicherstellen, dass das Programm beim Beenden alle Motoren stoppt.
- Das Fahrzeug während des Tests nicht unbeaufsichtigt betreiben.

## Clean-Code-Umsetzung

Das Projekt berücksichtigt folgende Clean-Code-Grundsätze:

- Aussagekräftige Namen für Klassen, Funktionen, Variablen und Konstanten
- Trennung der Verantwortlichkeiten in einzelne Module
- Kurze Funktionen mit möglichst nur einer Aufgabe
- Wenige Funktionsargumente
- Benannte Konstanten statt schwer verständlicher Zahlen
- Vermeidung von wiederholtem Code
- Kommentare nur zur Erklärung wichtiger Absichten oder technischer Gründe
- Keine auskommentierten alten Codeblöcke
- Einheitliche Python-Formatierung

## Bekannte Grenzen

Die drei Sensoren liefern ausschließlich digitale Werte. Dadurch kennt die
Regelung nur wenige mögliche Linienpositionen. Eine feinere und ruhigere
Regelung wäre mit analogen Sensorwerten oder einer größeren Sensorleiste
möglich.

Die optimalen Werte für P-Faktor, D-Faktor und Geschwindigkeit hängen außerdem
von Motoren, Akkuspannung, Untergrund, Reifenhaftung, Linienbreite und
Sensoreinstellung ab. Deshalb müssen die Werte am realen Fahrzeug abgestimmt
werden.

## Lizenz

Die Lizenzierung des Projekts richtet sich nach der Lizenzdatei des
übergeordneten Repositorys.
