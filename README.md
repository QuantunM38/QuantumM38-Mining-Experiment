# QuantumM38 – Mining & Blockchain Experiment

## 📌 Projektübersicht
QuantumM38 ist ein experimentelles Blockchain-Projekt, das die grundlegenden
Mechanismen von Proof-of-Work, Mining, Difficulty-Anpassung und Blockchain-
Validierung praktisch demonstriert.

Dieses Projekt dient **reinen Lern- und Demonstrationszwecken**.
Es werden **keine echten Coins**, **keine Tokens** und **kein echtes Geld** verwendet.

---

## 🎯 Ziel des Projekts
- Verstehen, wie Mining wirklich funktioniert
- Proof-of-Work praktisch umsetzen
- Difficulty & Target wie bei Bitcoin nachvollziehen
- Blockchain-Verkettung verstehen
- Manipulation durch Validierung erkennen

---

## ⚙️ Funktionsweise

### 🔹 Mining
- SHA-256 Hashing
- Nonce-basierte Suche
- Target-System (Hash < Target)
- Automatische Difficulty-Anpassung

### 🔹 Blockchain
- Mehrere Blöcke
- Jeder Block enthält den Hash des vorherigen Blocks
- Manipulation bricht die Kette

### 🔹 Validierung
Ein separates Skript überprüft:
- korrekten previous_hash
- unveränderte Hashes

Manipulierte Blöcke werden als **UNGÜLTIG** erkannt.

---

## 📂 Projektstruktur

quantum_mining_experiment/
├── mining.py
├── validate_chain.py
├── README.md
└── blocks/
├── block_1.json
├── block_2.json
├── block_3.json
├── block_4.json
└── block_5.json


---

## ▶️ Ausführen

### Mining starten
```bash
python mining.py

Blockhain Prüfen 

python validate_chain.py