"""Contractcatalogus. Onderzoeksagenten zijn uitbreidingspunten, geen fictieve AI-signalen."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Component:
    id: str
    kind: str
    responsibility: str
    dependencies: tuple[str, ...]


COMPONENTS = (
    Component('scanner', 'deterministic', 'Selecteer liquide EUR spotparen', ()),
    Component('regime', 'research', 'Classificeer marktregime', ('technical',)),
    Component('technical', 'deterministic', 'Bereken indicatoren', ('scanner',)),
    Component('multi_timeframe', 'deterministic', 'Vergelijk tijdsframes', ('technical',)),
    Component('sentiment', 'research', 'Onderzoek nieuws en sentiment', ('scanner',)),
    Component('quant', 'research', 'Onderzoek kwantitatieve hypothesen', ('regime', 'technical')),
    Component('entry', 'research', 'Stel instapvoorwaarden voor', ('multi_timeframe', 'sentiment', 'quant')),
    Component('exit', 'research', 'Stel uitstapvoorwaarden voor', ('multi_timeframe',)),
    Component('decision', 'deterministic', 'Combineer geldige signalen tot voorstel', ('entry', 'exit', 'regime')),
    Component('optimizer', 'research', 'Vraag backtests aan; stel kandidaten voor', ('quant',)),
    Component('risk', 'deterministic', 'Handhaaf harde en operationele limieten', ('decision',)),
    Component('execution', 'deterministic', 'Registreer uitsluitend virtuele ordervoorstellen', ('risk',)),
    Component('portfolio', 'deterministic', 'Gedeeld EUR saldo en boekhoudinterface', ('execution',)),
)
