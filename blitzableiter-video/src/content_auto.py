# -*- coding: utf-8 -*-
"""Short: Warum bist du im Auto bei einem Blitzschlag sicher? (Sprachspur: TTSMaker-MP3 des Nutzers).

Cabrio- und Wohnwagen-Satz wurden aus der Aufnahme geschnitten (Cabrio-Aussage war falsch).
"""
from content import spoken  # noqa: F401

CHAPTERS = [
    {"id": "hook", "label": None, "title": "Sicher im Auto?",
     "hook_title": [("SICHER", "w"), ("IM AUTO?", "y")],
     "keywords": ["Auto", "Blitzschlag", "sicher", "Gummireifen", "stimmt nicht"],
     "sentences": [("Warum bist du im Auto bei einem Blitzschlag sicher?", None),
                   ("Viele denken, wegen der Gummireifen.", None),
                   ("Aber das stimmt nicht.", None)]},
    {"id": "gummi", "label": "1", "title": "Gummireifen?",
     "keywords": ["mehrere Kilometer", "Luft", "Zentimeter Gummi"],
     "sentences": [("Ein Blitz ist so stark, dass er mehrere Kilometer Luft durchschlägt.", None),
                   ("Ein paar Zentimeter Gummi halten ihn nicht auf.", None)]},
    {"id": "grund", "label": "2", "title": "Der wahre Grund",
     "keywords": ["Metallhülle", "leichtesten Weg", "außen", "Karosserie", "nicht durch den Innenraum", "fast nichts"],
     "sentences": [("Der wahre Grund ist die Metallhülle des Autos.", None),
                   ("Wenn der Blitz einschlägt, sucht sich der Strom den leichtesten Weg.", None),
                   ("Und der führt außen an der Karosserie entlang, nicht durch den Innenraum.", None),
                   ("Im Inneren spürst du davon fast nichts.", None)]},
    {"id": "tipps", "label": "3", "title": "Wichtig",
     "keywords": ["Schäden", "Elektronik", "Fenster zu", "keine Metallteile", "Karosserie"],
     "sentences": [("Das Auto selbst kann aber Schäden bekommen, zum Beispiel an der Elektronik.", None),
                   ("Deshalb gilt im Gewitter: Fenster zu und fass keine Metallteile an, die mit der Karosserie verbunden sind.", None)]},
    {"id": "outro", "label": None, "title": "", "hook_title": [],
     "keywords": ["Wissen", "Folge"],
     "sentences": [("Mehr Wissen, kurz erklärt.", None), ("Folge mir!", None)]},
]
