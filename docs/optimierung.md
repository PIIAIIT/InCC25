
# Arten
maschinenunabhängig

lokale 
blockebene optimieren
gloabel
über blockebene

1. Kontrollflussanalyse
  - Goto statements
2. Datenflussanaylse
  - sammelt infos über den fluss der daten

# Kontrollflussanalyse
- Startpunkt: Betreten einer Funktion oder ein Sprunglabel
- Ende: Sprungbefehle oder Return 
- Der letzte Befehl eines Blocks zeigt immer auf den Anfang eines anderen Blocks

# Datenflussanaylse
- liveness
  - wird rückwärts analysiert
- NetworkX Algorithmus von Johnson
