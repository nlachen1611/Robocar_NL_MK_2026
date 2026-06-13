Raspberry Pi Line Follower
Projektbeschreibung

Ziel des Projekts ist die Entwicklung eines Linienfolgers mit einem Raspberry Pi. Das Fahrzeug folgt einer schwarzen Linie mithilfe von drei Liniensensoren und einer PD-Regelung. Wird die Linie kurzzeitig verloren, sucht das Fahrzeug anhand der zuletzt bekannten Linienposition selbstständig nach der Strecke.

Hardware
Raspberry Pi
PCA9685 PWM-Modul
4 Gleichstrommotoren
3 digitale Liniensensoren
Fahrgestell mit Spannungsversorgung
Softwareaufbau

Die Software besteht aus folgenden Hauptkomponenten:

LineFollower

Zentrale Steuerlogik des Fahrzeugs. Liest die Sensoren aus, berechnet den Regelfehler und steuert die Motoren.

LineSensors

Verwaltet die drei Liniensensoren und erkennt schwarze bzw. weiße Flächen.

MotorController

Steuert die vier Motoren über das PCA9685 PWM-Modul an.

LineFollowerConfig

Enthält alle einstellbaren Parameter wie Geschwindigkeit und Reglerwerte.

Funktionsweise
Sensorwerte werden eingelesen.
Die Position der Linie wird bestimmt.
Ein PD-Regler berechnet die notwendige Lenkkorrektur.
Die Motoren werden entsprechend angesteuert.
Wird keine Linie erkannt, startet ein Suchmodus.
Nach dem Wiederfinden der Linie wird die Regelung fortgesetzt.
Regelungsprinzip

Der Regelfehler wird aus den drei Sensorwerten berechnet:

Links = -1
Mitte = 0
Rechts = +1

Die Korrektur erfolgt über einen PD-Regler:

Korrektur = kp · Fehler + kd · Fehleränderung

Dadurch reagiert das Fahrzeug sowohl auf die aktuelle Abweichung als auch auf deren Änderung.

Projektziel

Das Fahrzeug soll einer schwarzen Linie möglichst stabil folgen und kurze Unterbrechungen der Strecke selbstständig überwinden.
