# Validierungsreparatur – 30. Oktober 2026

Basis: `29942d85bf5191d39e970e12cddd3637267215cc`.
Umgebung: Linux, Python 3.12.14, Python-Standardbibliothek.

## Befund und Reparatur

Der bisherige Validator überspringt den Genesisblock vollständig und prüft
keinen Proof of Work. Der ausgeführte Vorher/Nachher-Versuch bestätigt:
Eine Änderung der Genesisdaten bei unverändertem gespeicherten Hash wird
vorher akzeptiert und danach abgewiesen. Auch ein korrekt neu berechneter,
aber zu großer Genesis-Hash wird vorher akzeptiert und danach abgewiesen.
Siehe `before-after-results.txt`.

Der neue Validator prüft Schema, Typen, fortlaufende IDs, Genesis-Vorgänger
(64 Nullen), Verkettung, Hash-Neuberechnung und PoW auch für Block 1.
Genesis verwendet `2**240`, jeder Folgeblock das geprüfte `new_target` seines
Vorgängers. Der Vergleich ist strikt `Hash < Target`, passend zu mining.py.
Das eigene `new_target` eines Blocks gilt ausdrücklich erst danach.
Target-Manipulationen werden gegen die bestehende Anpassungsregel geprüft;
bei ungültigem Target wird abgebrochen, statt damit weitere PoW zu legitimieren.
Die Float-Arithmetik des bisherigen Miners bleibt zur Kompatibilität erhalten.

Dateien werden numerisch sortiert, fehlende Nummern, leere Verzeichnisse,
fremde Einträge, defektes JSON und doppelte JSON-Schlüssel werden abgewiesen.
Der Import hat keine Seiteneffekte. CLI: Exit 0 gültig, Exit 1 ungültig oder
nicht lesbar. Der Validator schreibt keine Blockdateien.

## Tatsächlich ausgeführte Tests

```
python -m unittest discover -s tests -v
```

23 Tests bestanden, 0 fehlgeschlagen (0.301 Sekunden im dokumentierten Lauf).
Der vollständige Output steht in `test-results.txt`. Die Tests erzeugen eigene
PoW-Fixtures mit dem echten Start-Target in Speicher bzw. temporären Ordnern.
Abgedeckt sind Daten-/Nonce-Manipulationen in Genesis und Folgeblock,
Genesis-Vorgänger, Verkettung, Hash-konsistente ungültige PoW, Target-Grenzwert,
Target-Erhöhung, Vorblock-Target, Rundungsgrenze, ungültige Felder, IDs,
Dateireihenfolge bis Block 11, Ladefehler, CLI-Exitcodes und Schreibfreiheit.

```
python validate_chain.py
```

Originalkette: **UNGÜLTIG**, Exit 1. Block 3 enthält einen gespeicherten Hash,
der nicht zu seinen Daten passt; Block 4 verweist auf einen anderen Hash.
Schon der alte Validator meldet diese beiden Fehler, beendet sich aber mit 0.
Die Reparatur kaschiert diesen bestehenden Befund nicht.
Alle fünf Originaldateien wurden byteweise mit dem Basis-Commit verglichen:
unverändert. SHA-256-Werte stehen in `original-blocks.sha256`.
`mining.py` wurde weder verändert noch ausgeführt, weil es Originalblöcke
überschreiben würde.

## Grenzen des bestehenden Formats

„Vollständig“ bedeutet hier: alle prüfbaren Regeln des bestehenden Lernformats
für jeden Block, einschließlich Genesis. Es bedeutet keine Bitcoin-Sicherheit.
Nur `data`, `previous_hash` und `nonce` sind im Hash gebunden. Zeitstempel,
Block-ID, Laufzeit und neues Target sind keine kryptografisch gebundenen Felder.
Schema-/Regelprüfung kann Änderungen erkennen, aber nicht jede plausible
Metadatenmanipulation. Laufzeiten sind nicht unabhängig nachprüfbar.
Da der Miner die Laufzeit erst nach der Difficulty-Entscheidung auf drei
Nachkommastellen rundet, sind bei gespeicherten 3.000 Sekunden beide Zweige
zulässig. Diese Information ist in Altblöcken nicht rekonstruierbar.
Es gibt keinen extern verankerten Genesis-Hash oder erwarteten Endblock:
Eine vollständig neu geminte Kette bzw. ein gültiges Präfix ist nicht als
Austausch/Abschneiden erkennbar. Ein neues versioniertes Format mit gebundenem
Target und Zeitstempel wäre ein separates Vorhaben und würde neue Blöcke
benötigen. Die Originaldateien werden hierfür nicht migriert.

## Unterschiede zu Bitcoin

Dieses Projekt hasht einmal SHA-256 über eine Textverkettung und passt die
Difficulty nach jedem Block anhand lokal gemessener Laufzeit an (Ziel 3 s).
Bitcoin verwendet doppeltes SHA-256 über einen binären 80-Byte-Header,
Transaktionen mit Merkle-Root, ein im Header kodiertes Target und
netzwerkweite Konsensregeln. Bitcoin-Mainnet zielt im Mittel auf 10 Minuten
und passt die Difficulty alle 2016 Blöcke an. Nodes prüfen Transaktionen,
Signaturen, Ausgaben und die Kette mit der größten kumulierten Arbeit.
Das Lernprojekt hat weder dieses Netzwerk noch echte Bitcoin-Transaktionen
oder gültige Bitcoin-Blockbelohnungen. Seine Hashfunde erzeugen keine Bitcoins.
Quelle: https://developer.bitcoin.org/devguide/block_chain.html
Header: https://developer.bitcoin.org/reference/block_chain.html
