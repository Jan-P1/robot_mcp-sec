Kurze Projektbeschreibung:

Im Labor für Cyber-Physische Systeme wird ein System entwickelt, das die Steuerung eines Roboterarms (Niryo Ned2) über natürliche Sprache ermöglicht. Nutzeranweisungen wie „Hebe den Stift auf und lege ihn neben den roten Würfel" werden von einem großen Sprachmodell (LLM) interpretiert und über das Model Context Protocol (MCP) in konkrete Roboterbefehle umgewandelt.
Da das System sprachgesteuert ist und direkt mit physischer Hardware interagiert, entstehen neuartige Sicherheitsrisiken: Ein Nutzer – oder ein Angreifer – könnte Anweisungen formulieren, die den Roboter in gefährliche Betriebszustände versetzen, Sicherheitsgrenzen überschreiten oder durch verschleierte Formulierungen (Prompt Injection) unerwünschte Aktionen auslösen.

In dieser Arbeit soll ein SafeGuard-Modul entwickelt werden, das vor das LLM geschaltet wird und eingehende Nutzeranweisungen auf Sicherheitsrisiken prüft, bevor sie zur Interpretation weitergereicht werden. Das Modul soll:
1. Policy-basierte Filterung: Eine konfigurierbare Regelstruktur, in der erlaubte und verbotene Aufgaben oder Aufgabenkategorien hinterlegt werden können (z. B. als YAML- oder JSON-Konfiguration). Beispiele: Bewegungen außerhalb des Arbeitsraums sind verboten; das Aufheben von Objekten ist erlaubt. Die Konfiguration soll ohne Programmieraufwand anpassbar sein.
2. Erkennung potenziell gefährlicher Anweisungen: Semantische Klassifikation eingehender Anweisungen – auch solcher, die die Gefährlichkeit sprachlich verschleiern (z. B. Umschreibungen, mehrdeutige Formulierungen). Hier soll untersucht werden, wie LLM-basierte Klassifikatoren, regelbasierte Ansätze oder hybride Verfahren geeignet eingesetzt werden können.
3. Erkennung von Prompt Injection: Angriffe, bei denen gefährliche Anweisungen in scheinbar harmlose Eingaben eingebettet werden (z. B. in Objektbeschriftungen, die die Kamera liest, oder in sprachlich manipulierten Eingaben), sollen zuverlässig erkannt und geblockt werden.
4. Stresstest und Evaluation: Nach der Implementierung soll ein systematischer Stresstest durchgeführt werden. Dazu ist ein Katalog von Angriffsszenarien zu entwickeln (direkter Angriff, indirekte Injektion, graduell versteckte Formulierungen, mehrsprachige Angriffe u. a.) und die Erkennungsrate sowie die False-Positive-Rate zu messen und zu diskutieren.

Wissenschaftliche Fragestellungen
Welche Klassen von Sicherheitsrisiken entstehen bei sprachgesteuerten Robotersystemen, und wie lassen sie sich systematisch kategorisieren?
Wie zuverlässig können LLM-basierte Klassifikatoren gefährliche oder unzulässige Anweisungen erkennen – auch in verschleierter Form?
Wie ist ein policy-basiertes Regelwerk sinnvoll zu strukturieren, damit es von nicht-technischen Nutzern konfigurierbar ist?
Welche Angriffsmuster auf Prompt-Injection-Ebene sind im Kontext physischer Robotersysteme besonders kritisch?