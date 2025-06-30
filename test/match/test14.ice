{
erg := vergleiche 1 mit
    fall 0 : "null" .
    fall 1 : "eins" .
    fall 2 : "zwei" .
    fall _ : "anders" .
.;
assert := erg = "eins";

erg := vergleiche 42 mit
    fall 1 : "eins" .
    fall 2 : "zwei" .
    fall _ : "unbekannt" .
.;
assert +:= erg = "unbekannt";

erg := vergleiche "hi" mit
    fall "hello" : 1 .
    fall "hi"    : 2 .
    fall _       : 3 .
.;
assert +:= erg = 2;

x := 3;
erg := vergleiche x + 1 mit
    fall 3 : "drei" .
    fall 4 : "vier" .
    fall _ : "??" .
.;
assert +:= erg = "vier";

erg := vergleiche 2 mit
    fall 2 : "zwei" .
    fall 2 : "doppelt" .
    fall _ : "sonst" .
.;
assert +:= erg = "zwei";

erg := vergleiche [1, 2, 3] mit
    fall [1, 2, 3] : "korrekt" .
    fall [1, 2, c] : "drei-elementig" .
    fall [1, b, c] : "drei-elementig" .
    fall [1, 2]    : "zwei-elementig" .
    fall _         : "keine Ahnung" .
.;
assert +:= erg = "korrekt";

Person := struct { name := "Alice", alter := 30 };
erg := vergleiche Person mit
    fall struct { name := alt, alter := 30 } : alt .
    fall _ : "nomatch" .
.;
assert +:= erg = "Alice";

erg := vergleiche 99 mit
    fall 1 : "eins" .
    fall 2 : "zwei" .
.;
assert +:= erg = leere;
assert = 8
}
