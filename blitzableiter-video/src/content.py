# -*- coding: utf-8 -*-
"""Gesprochener Text, Kapitel und Untertitel-Schlüsselwörter.

Jeder Satz ist ein Paar (Untertitel-Text, gesprochener Text oder None).
None = gesprochen wird genau der Untertitel-Text (nach TTS_FIX).
Zahlen stehen im Untertitel als Ziffern, gesprochen als Wort - der Inhalt ist identisch.
"""

# Nur für die Aussprache der TTS-Stimme. Ändert keine Inhalte.
TTS_FIX = [
    ("Benjamin Franklin", "Bänjamin Fränklinn"),
    ("Überspannungsschutz", "Überspannungs-Schutz"),
    ("Spannungsspitzen", "Spannungs-Spitzen"),
    ("Sicherungskasten", "Sicherungs-Kasten"),
    ("Steckdosenleiste", "Steckdosen-Leiste"),
    ("Erdboden", "Ehrdboden"),
    ("Erdung", "Ehrdung"),
    ("Ampere", "Ampär"),
    ("aneinander", "ann-einander"),
]

CHAPTERS = [
    {
        "id": "intro", "label": None, "title": None,
        "keywords": ["Blitz", "Sonne", "Ampere", "Metallstange", "Blitzableiter", "anzieht"],
        "sentences": [
            ("Ein Blitz ist heißer als die Oberfläche der Sonne und hat rund 20.000 Ampere.",
             "Ein Blitz ist heißer als die Oberfläche der Sonne und hat rund zwanzigtausend Ampere."),
            ("Trotzdem steht auf vielen Dächern nur eine dünne Metallstange, und das Haus bleibt heil.", None),
            ("Wie kann das sein?", None),
            ("Und stimmt es, dass ein Blitzableiter Blitze anzieht?", None),
            ("Das klären wir in den nächsten fünf Minuten.", None),
        ],
    },
    {
        "id": "k1", "label": "Kapitel 1", "title": "Wie entsteht ein Blitz?",
        "keywords": ["Blitz", "Eis", "Wassertropfen", "positiv", "negativ", "Spannung", "Millionen Volt",
                     "leitfähig", "30.000 Grad", "Donner"],
        "sentences": [
            ("Fangen wir mit dem Blitz an.", None),
            ("In einer Gewitterwolke reiben Eis und Wassertropfen aneinander.", None),
            ("Dadurch laden sich Teile der Wolke elektrisch auf, oben positiv und unten negativ.", None),
            ("Zwischen Wolke und Erdboden baut sich eine gewaltige Spannung auf, viele Millionen Volt.", None),
            ("Irgendwann hält die Luft das nicht mehr aus.", None),
            ("Sie wird leitfähig, und ein Strom springt über.", None),
            ("Das ist der Blitz.", None),
            ("Dabei erhitzt er die Luft auf rund 30.000 Grad.",
             "Dabei erhitzt er die Luft auf rund dreißigtausend Grad."),
            ("Die Luft dehnt sich schlagartig aus, und genau das hören wir als Donner.", None),
        ],
    },
    {
        "id": "k2", "label": "Kapitel 2", "title": "Das Problem",
        "keywords": ["ohne Schutz", "Gebäude", "Feuchtigkeit", "verdampft", "Brand", "Blitzableiter"],
        "sentences": [
            ("Jetzt stell dir ein Haus vor.", None),
            ("Schlägt der Blitz ohne Schutz ein, sucht sich der Strom den Weg durch das Gebäude.", None),
            ("Er fließt durch Holzbalken, Wände und Leitungen.", None),
            ("Die Feuchtigkeit im Holz verdampft schlagartig, und Dachstühle können in Brand geraten.", None),
            ("Genau dafür wurde der Blitzableiter erfunden.", None),
        ],
    },
    {
        "id": "k3", "label": "Kapitel 3", "title": "Die Geschichte",
        "keywords": ["18. Jahrhunderts", "Benjamin Franklin", "elektrische Entladungen", "Metallstangen",
                     "Erde", "Standard"],
        "sentences": [
            ("Erfunden wurde er Mitte des 18. Jahrhunderts.",
             "Erfunden wurde er Mitte des achtzehnten Jahrhunderts."),
            ("Der amerikanische Wissenschaftler Benjamin Franklin hatte die Idee, dass Blitze elektrische Entladungen sind.", None),
            ("Er schlug vor, spitze Metallstangen auf Gebäuden anzubringen und den Strom über ein Kabel sicher in die Erde zu leiten.", None),
            ("Damals war das neu, denn niemand wusste genau, was ein Blitz überhaupt ist.", None),
            ("Heute gehört der Blitzschutz bei vielen Gebäuden zum Standard.", None),
        ],
    },
    {
        "id": "k4", "label": "Kapitel 4", "title": "Die drei Teile",
        "keywords": ["drei Teilen", "Erstens", "Fangeinrichtung", "Zweitens", "Ableitung", "Drittens", "Erdung",
                     "höchsten Punkten", "schmilzt", "Fundament", "Erde", "zusammenpassen"],
        "sentences": [
            ("Ein klassischer Blitzableiter besteht aus drei Teilen.", None),
            ("Erstens: die Fangeinrichtung.", None),
            ("Das sind Metallstangen oder Drähte ganz oben auf dem Dach, an den höchsten Punkten.", None),
            ("Sie fangen den Blitz auf, damit er nicht irgendwo ins Dach einschlägt.", None),
            ("Zweitens: die Ableitung.", None),
            ("Dicke Kabel oder Metallbänder führen außen an der Hauswand nach unten.", None),
            ("Sie sind so dick, damit der riesige Strom sie nicht schmilzt.", None),
            ("Drittens: die Erdung.", None),
            ("Am Boden enden die Leitungen in Metallstäben oder einem Metallband im Fundament.", None),
            ("Dort verteilt sich der Strom in der Erde, ohne Schaden anzurichten.", None),
            ("Wichtig ist, dass alle drei Teile zusammenpassen.", None),
            ("Ist die Erdung schlecht, sucht sich der Strom doch wieder einen anderen Weg.", None),
        ],
    },
    {
        "id": "k5", "label": "Kapitel 5", "title": "Der große Irrtum",
        "keywords": ["Irrtum", "zieht Blitze an", "stimmt nicht", "hoch", "frei stehend", "nicht gefährdeter",
                     "sicheren", "Weg", "irreführend", "Schaden"],
        "sentences": [
            ("Jetzt zum größten Irrtum.", None),
            ("Viele glauben, ein Blitzableiter zieht Blitze an.", None),
            ("Das stimmt nicht.", None),
            ("Ob ein Blitz einschlägt, hängt vor allem davon ab, wie hoch und frei stehend ein Gebäude ist.", None),
            ("Der Blitzableiter macht das Haus nicht gefährdeter.", None),
            ("Er sorgt nur dafür, dass der Blitz einen sicheren, vorbereiteten Weg bekommt, statt durch das Haus zu laufen.", None),
            ("Auch der Name ist etwas irreführend.", None),
            ("Er leitet den Blitzstrom ab, er verhindert keinen Blitz.", None),
            ("Er verhindert nur den Schaden.", None),
        ],
    },
    {
        "id": "k6", "label": "Kapitel 6", "title": "Der innere Blitzschutz",
        "keywords": ["Felder", "Spannungsspitzen", "Fernseher", "Router", "Computer", "innere Blitzschutz",
                     "Überspannungsschutz", "äußere Blitzschutz", "Gebäude", "Elektronik"],
        "sentences": [
            ("Aber selbst mit Blitzableiter gibt es ein Problem.", None),
            ("Schlägt ein Blitz in der Nähe ein, entstehen starke elektrische und magnetische Felder.", None),
            ("Sie können in Leitungen kurze, hohe Spannungsspitzen erzeugen.", None),
            ("Das gefährdet Fernseher, Router und Computer.", None),
            ("Deshalb gibt es zusätzlich den inneren Blitzschutz, zum Beispiel einen Überspannungsschutz in der Steckdosenleiste oder im Sicherungskasten.", None),
            ("Der äußere Blitzschutz schützt das Gebäude, der innere die Elektronik.", None),
        ],
    },
    {
        "id": "k7", "label": "Kapitel 7", "title": "Wo ist er Pflicht?",
        "keywords": ["Nein", "Landesbauordnungen", "viele Menschen", "besonders hoch", "Krankenhäuser",
                     "Hochhäuser", "Versammlungsstätten", "freiwillig", "sinnvoll", "Bundesland"],
        "sentences": [
            ("Muss jedes Haus einen Blitzableiter haben?", None),
            ("Nein.", None),
            ("In Deutschland regeln das die Landesbauordnungen.", None),
            ("Vorgeschrieben ist er meist bei Gebäuden, in denen viele Menschen zusammenkommen oder die besonders hoch sind, zum Beispiel Krankenhäuser, Hochhäuser oder große Versammlungsstätten.", None),
            ("Bei normalen Wohnhäusern ist er oft freiwillig, aber sinnvoll.", None),
            ("Die genauen Regeln hängen vom Bundesland und vom Gebäude ab.", None),
        ],
    },
    {
        "id": "k8", "label": "Kapitel 8", "title": "Was du selbst tun kannst",
        "keywords": ["Gebäude", "Auto", "freie Flächen", "einzelne Bäume", "Wasser", "Steckdose", "sicherste Schutz"],
        "sentences": [
            ("Und was kannst du selbst tun?", None),
            ("Such bei einem Gewitter ein Gebäude oder ein Auto auf.", None),
            ("Meide freie Flächen, einzelne Bäume und Wasser.", None),
            ("Und wenn du Zeit hast, zieh empfindliche Geräte aus der Steckdose.", None),
            ("Das ist der sicherste Schutz für deine Elektronik.", None),
        ],
    },
    {
        "id": "outro", "label": "Schluss", "title": "Zusammenfassung",
        "keywords": ["keine Blitze", "sicheren Weg", "Fangen", "Ableiten", "Erden", "innere Blitzschutz",
                     "Like", "abonniere"],
        "sentences": [
            ("Fassen wir zusammen: Ein Blitzableiter zieht keine Blitze an.", None),
            ("Er gibt dem Blitz einen sicheren Weg: Fangen, Ableiten, Erden.", None),
            ("Und der innere Blitzschutz kümmert sich um deine Elektronik.", None),
            ("Wenn dir das Video gefallen hat, lass ein Like da und abonniere für mehr Wissen, kurz erklärt.", None),
        ],
    },
]


def spoken(display, override):
    text = override if override else display
    for a, b in TTS_FIX:
        text = text.replace(a, b)
    return text
