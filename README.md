
<!-- ![Logo](logo.jpg) -->
<p align="center">
  <img src="logo.jpg" alt="IceMango" width="500">
</p>

# ICE – Interpreter für Interpreter und Compilerbau


Dieses Projekt implementiert meine Ice-Sorte: Mango - einen Interpreter im Rahmen der Veranstaltung „Interpreter und Compilerbau Entwicklung“. Der Code dient als praktisches Beispiel für die Entwicklung von Interpretern und bietet eine Grundlage für das Verständnis von Compilerbau.


## 📦 Übersicht

- Das Repository enthält die folgenden Hauptkomponenten:
- **Lexer**: Tokenisiert den Quellcode in lexikalische Einheiten.
- **Parser**: Analysiert die Syntax des Quellcodes und erstellt eine abstrakte Syntaxbaum (AST).
- **Interpreter**: Führt den AST aus und gibt die Ergebnisse aus.
- **Standardbibliothek**: Enthält grundlegende Funktionen.
- **Testumgebung**: Stellt sicher, dass der Interpreter korrekt funktioniert.
## ⚙️ Installation

Clone das Repository und navigiere in das Projektverzeichnis:

```bash
  git clone https://github.com/PIIAIIT/InCC25.git
  cd InCC25
```

Stelle sicher, dass Python 3 installiert ist.


## 🚀 Nutzung

Verwende `make`, um verschiedene Teile des Interpreters auszuführen:

```bash
  make [command]
```
Verfügbare Befehle:
- `lexer`: Führt den Lexer aus.
- `parser`: Führt den Parser aus.
- `test`: Führt die Tests aus.
- `debug`: Startet den Debugger. Mit allen Debug Infos.
Wenn kein Befehl angegeben wird, startet die interaktive Shell des Interpreters.
> Für die Semantik der Sprache verweise ich auf die [Datei](HOW_TO_CODE.md).




## 🧪 Tests

Das Projekt enthält eine Testumgebung, um die Funktionalität des Interpreters zu überprüfen. Führe die Tests mit dem folgenden Befehl aus:


```bash
  make test
```
Dies stellt sicher, dass alle Komponenten wie erwartet funktionieren.



## 📚 Weitere Informationen

Für eine detaillierte Beschreibung der Implementierung und der verwendeten Techniken siehe die einzelnen Moduldateien im Repository.


## License

[MIT](https://choosealicense.com/licenses/mit/)
