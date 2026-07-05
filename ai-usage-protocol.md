# KI-Nutzungsprotokoll zur Studienarbeit

## Angaben zur Arbeit

- Gruppenname:
- Titel der Studienarbeit:
- KI genutzt: ja / nein
- Verwendete KI-Werkzeuge:

Wenn keine KI genutzt wurde, reicht hier die Angabe "nein". In diesem Fall müssen die folgenden Abschnitte nicht
ausgefüllt werden.

## Kurz-Erklärung

Dieses Protokoll wird als Markdown-Datei im Git-Repository der Gruppe geführt.
Wesentliche KI-Nutzungen werden hier kurz und zeitnah dokumentiert.
Die Nachvollziehbarkeit über Versionen ergibt sich aus der Git-Historie dieser Datei.

Für diese Studienarbeit wurden KI-Werkzeuge als Unterstützung verwendet.
Die wesentlichen Nutzungen sind unten dokumentiert.
Alle übernommenen Inhalte wurden fachlich geprüft, bei Bedarf angepasst und in die Arbeit eigenverantwortlich
integriert.

## Übersicht der KI-Nutzung

Tragen Sie hier die wesentlichen Nutzungen ein.
Wenn ähnliche Nutzungen in engem Zusammenhang stehen, können Sie sie zusammenfassen.
Pflegen Sie das Protokoll möglichst zeitnah, damit die Git-Historie die Entwicklung nachvollziehbar macht. Nutzen Sie
KI, um Ihren Promtverlauf entsprechnd dieser Vorlage festzuhalten.

| Datum      | Anwender der KI | Werkzeug | Nutzung kurz beschrieben                                                                                                                                    | Übernahme und Anpassung kurz beschrieben                                                                                                        |
|------------|-----------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| 2026-04-04 | Karla           | ChatGPT  | SQLAlchemy + Flask App-Init, Tabellen-Erstellung, App Context, Sequence/Unique Issues                                                                       | Beispiele für Standardnutzung, Bug fixes nach Implementierung                                                                                   |
| 2026-04-13 | Karla           | ChatGPT  | Hexagonale Architektur + Flask Design diskutiert (Repository Pattern, Protocols, Dependency Injection)                                                      | Refactoring-Ansatz entwickelt: Entkopplung von DB-Zugriffen über Interfaces/Protocols                                                           |
| 2026-04-14 | Karla           | ChatGPT  | Konzept für globale Validierung / API Setup-Struktur in Flask                                                                                               | Architekturentscheidung: Validierung zentral durch openAPI in App-Setup integriert statt verteilt                                               |
| 2026-04-16 | Karla           | ChatGPT  | MinIO Integration + presigned URL Probleme in Docker (localhost vs. container network), Image Delivery Design                                               | Umstellung auf Backend-Proxy für Bilder (Flask Route statt presigned URLs), URL-Handling + Encoding angepasst                                   |
| 2026-04-26 | Nia             | ChatGPT  | Generierung der yaml routen.                                                                                                                                | Generierung des Codes von vordefinierten Routen (anhand unseres Designs und definierten Statuscodes). Anpassung der Beschreibungen und Schemas. |
| 2026-05-14 | Pratham         | ChatGPT  | Unterstützung bei Planung der Service-Struktur für den Scan-Flow (Orchestrierung statt Logik im Controller)                                                 | Strukturvorschläge geprüft und manuell umgesetzt: `ScanService` als Orchestrator, Controller weiterhin schlank                                  |
| 2026-05-14 | Pratham         | ChatGPT  | Unterstützung bei Design und Fehlerbehandlung für `RecognitionService` + LISA-Anbindung                                                                     | Bestehende Trennung beibehalten (Recognition nur Bilderkennung), Fehlerpfade getestet und projektkonform angepasst                              |
| 2026-05-14 | Pratham         | ChatGPT  | Hilfe bei Entwurf von `SummaryService`/`LisaSummaryApiClient` inkl. Fallback-Idee                                                                           | Implementierung eigenständig integriert, Prompt/Antwortformat und Fallback-Verhalten fachlich geprüft                                           |
| 2026-05-14 | Pratham         | ChatGPT  | Unterstützung bei Persistenz-Erweiterung (`card_summary`, Card-Insert, Image-Referenz, DB-Schema-Sync)                                                      | Vorschläge selektiv übernommen, SQLAlchemy-Modelle/Repos manuell nachgezogen und gegen Laufzeit geprüft                                        |
| 2026-05-14 | Pratham         | ChatGPT  | Hilfe bei API/DTO/Test-Anpassungen (Scan-Response, OpenAPI, Unit-Tests, Troubleshooting)                                                                    | Antworten/Tests manuell verifiziert, reale End-to-End Calls ausgeführt und nur passende Teile übernommen                                        |
| 2026-05-24 | Pratham         | ChatGPT  | Strukturhilfe für `CollectionService` (Service/Repository/DTO/Route-Aufteilung), inkl. Such-/Sort-/Filter-Use-Cases                                         | KI als Sparringspartner für Architektur genutzt; teilweise Snippets übernommen, projektkonform angepasst und wesentliche Teile eigenständig implementiert/verifiziert |
| 2026-06-24 | Pratham         | ChatGPT  | Planungshilfe für Kategorie-Zuweisung im Scan-Flow (`CategoryService`, LISA-Kategorieadapter, Threshold/Fallback, manuelle Korrektur im Collection-Kontext) | KI für Ablauf- und Strukturplanung genutzt; Fachlogik, erlaubte Kategorien, Threshold-Verhalten, Tests und Integration eigenständig geprüft und an Projektarchitektur angepasst |
| 2026-07-01 | Lukas           | ChatGPT  | Architektur Struktur Unterstüzung für das Planen eines Achievement Update Services zum Prüfen ob der Nutzer dieses bereits erfüllt hat                      | KI als Berater bei Architektur und Vorgangsaufbau, empfahl update_progress route abzuschaffen und den Service diese Aufgabe übernehmen zu lassen | 
| 2026-07-02 | Pratham         | ChatGPT  | Unterstützung bei Analyse, an welchen Backend-Stellen HTTP-Caching fachlich sinnvoll ist (Wiki, Images, Collection, Scan/Auth `no-store`) und Planung der Umsetzung mit `Cache-Control`, `ETag`, `If-None-Match` und `If-Match` | KI für Architektur- und Umsetzungsplanung genutzt; einzelne Code-Snippets für Cache-Helper, Header-Handling und Tests teilweise übernommen, anschließend projektkonform angepasst, getestet und manuell verifiziert |


## Optionale ergänzende Hinweise

Hier können Sie bei Bedarf kurz ergänzen,

- wie Sie mit fehlerhaften KI-Antworten umgegangen sind,
- welche Vorschläge Sie bewusst verworfen haben,
- in welchen Fällen die KI nur als Sparringspartner diente.

## Eigenständigkeit und Verantwortung

Wir bestätigen, dass die KI-Nutzung in dieser Arbeit vollständig und nach bestem Wissen dokumentiert wurde.
Wir übernehmen die Verantwortung für die fachliche Richtigkeit, die Auswahl der übernommenen Inhalte und die gesamte
abgegebene Arbeit.

- Datum:
- Gruppenname:
