from dataclasses import dataclass


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
