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

Physische Risiken: Verletzungen an Personen, Schäden an Umgebung, Schäden an System selbst
Cyberphysische Risiken: Fernsteuerung/Hacking, Missbrauch der stimmbasierten Steuerung, Angriffe auf KIs (injection, adverserial, ...)
Data-/Privacy: LLM kann sensible Daten herausgeben je nach Zugriff und Filterung der Antworten (Nutzerdaten, Forschugsdaten), Mikrofon und Kamera immer an (wenn in Betrieb) -> Logging, streams 

---

Wie zuverlässig können LLM-basierte Klassifikatoren gefährliche oder unzulässige Anweisungen erkennen – auch in verschleierter Form?
Schwierig zu beantworten. LLMs sind im allgemeinen sehr anfällig für verschiedene Angriffe. Kodierung des Prompts (base64, Caesar-Schiffre, Leet-Speak), wenig gelernte Sprachen, Jailbreaking und Social Engineering sind gut dokumentierte Schwachstellen. Mit einer spezialisierten KI names "CHAI" wurden Angriffe auf verschiedene Cyber-Physische Systeme simuliert, mit großem Erfolg (Angriff, der Drohnen zum landen bringen soll: 68,1% Erfolg; Angriffe auf selbstfahrende Autos: 81,8% Erfolg; Drohne mit Angriff von Tracking abbringen: 95,5% Erfolg).

Allerdings gibt es auch gegenmaßnahmen:
### RoboGuard
RoboGuard wurde entwickelt von Forschern der University of Pennsylvania und Carnegie Mellon UNiversity. Im wesentlichen funktioniert es so, dass man ein separates "Root-of-Trust-LLM" verwendet, also ein anderes Model, das niemals direkt mit dem Prompt des Nutzers in Kontakt kommt und somit nicht kompromittiert wird. Mit einer Regelliste und einer Zusammenfassung oder den extrahierten MCP-Toolbefehlen des User-Prompt, verwendet das Model Chain-of-Thought

---

Wie ist ein policy-basiertes Regelwerk sinnvoll zu strukturieren, damit es von nicht-technischen Nutzern konfigurierbar ist?
Human readable, einfach verständlich, übersichtlich strukturiert
---

Welche Angriffsmuster auf Prompt-Injection-Ebene sind im Kontext physischer Robotersysteme besonders kritisch?
Jailbreaking und obfuscation, da Regeln ausgehebelt bzw. umgangen werden
---