AMD64 - x86_64
abwärtskompatible 64 Erweiterung der 80x86

CISC
RISC sind besser für einen Compiler

https://wiki.osdev.org/X86-64_Instruction_Encoding
https://wiki.osdev.org/System_V_ABI

# ELF Executable and Linkable Format
https://en.wikipedia.org/wiki/Executable_and_Linkable_Format

- Ablauf beim Laden
  - ELF Header lesen
  - Programm-Header lesen
  - Segmente in Speicher laden
  - Relokationen durchführen
  - Initialisierungsfunktionen aufrufen
  - Kontrolle an den Einstiegspunkt übergeben

Linker - ld-linux-x86-64

# Calling Conventions 
für Funktionen
Stack ist auf 16 Bytes aligned !!!
Kernel springt default auf _start
Parameterübergabe über Register (RSI, RDI, RSP, RSB, R8, R9)
Fließkommazahlen über XMM Register (xmm0 bis xmm7)

Beim call label wird 
- die Rücksprungadresse auf den Stack gelegt
- lieber mit sprung machen statt call wegen stackalignment
- syscall wird kein Sprungziel angegeben sondern in register rax

Register wird in 2 Gruppen geteilt.
caller-saved : rax, rdi ,rsi rdx, rcx, r8, r9, r10, r11
callee-saved : rbx, rsp, rbp, r12, r13, r14, r15

LEA : Gut für Closure
MOVS / MOVSB : Byteweise copy (rewrite)
PUSH / POP : Stack manipulation (immer 64 Bit)
