# -*- coding: utf-8 -*-
"""YouTube-Short: Kurzfassung aus Sätzen des Originaltexts (keine neuen Fakten)."""
from content import TTS_FIX, spoken  # noqa: F401  (gleiche Aussprache-Korrekturen)

CHAPTERS = [
    {
        "id": "hook", "label": None, "title": "Zieht er Blitze an?",
        "keywords": ["Blitzableiter", "Blitze", "Sonne", "Ampere", "Metallstange", "heil"],
        "sentences": [
            ("Zieht ein Blitzableiter Blitze an?", None),
            ("Ein Blitz ist heißer als die Oberfläche der Sonne und hat rund 20.000 Ampere.",
             "Ein Blitz ist heißer als die Oberfläche der Sonne und hat rund zwanzigtausend Ampere."),
            ("Trotzdem steht auf vielen Dächern nur eine dünne Metallstange, und das Haus bleibt heil.", None),
        ],
    },
    {
        "id": "teile", "label": "1", "title": "Die drei Teile",
        "keywords": ["drei Teilen", "Fangeinrichtung", "Ableitung", "Hauswand", "Erdung", "Erde", "Schaden"],
        "sentences": [
            ("Denn ein Blitzableiter besteht aus drei Teilen.", None),
            ("Die Fangeinrichtung oben auf dem Dach fängt den Blitz auf.", None),
            ("Die Ableitung führt den Strom außen an der Hauswand nach unten.", None),
            ("Und die Erdung verteilt ihn in der Erde, ohne Schaden anzurichten.", None),
        ],
    },
    {
        "id": "irrtum", "label": "2", "title": "Der Irrtum",
        "keywords": ["Blitze an", "Nein", "hoch", "frei stehend", "keinen Blitz", "Schaden"],
        "sentences": [
            ("Zieht er also Blitze an?", None),
            ("Nein.", None),
            ("Ob ein Blitz einschlägt, hängt vor allem davon ab, wie hoch und frei stehend ein Gebäude ist.", None),
            ("Der Blitzableiter verhindert keinen Blitz.", None),
            ("Er verhindert nur den Schaden.", None),
        ],
    },
    {
        "id": "fazit", "label": "3", "title": "Merke",
        "keywords": ["Fangen", "Ableiten", "Erden", "ganze Video", "Kanal"],
        "sentences": [
            ("Fangen, Ableiten, Erden.", None),
            ("Das ganze Video findest du auf meinem Kanal.", None),
        ],
    },
]
