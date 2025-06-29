{
_erg := vergleiche 1 mit
    fall 0 : "null" .
    fall 1 : "eins" .
    fall 2 : "zwei" .
    fall _ : "anders" .
.;
assert := _erg = "eins";

_erg := vergleiche 42 mit
    fall 1 : "eins" .
    fall 2 : "zwei" .
    fall _ : "unbekannt" .
.;
assert +:= _erg = "unbekannt";

_erg := vergleiche "hi" mit
    fall "hello" : 1 .
    fall "hi"    : 2 .
    fall _       : 3 .
.;
assert +:= _erg = 2;

x := 3;
_erg := vergleiche x + 1 mit
    fall 3 : "drei" .
    fall 4 : "vier" .
    fall _ : "??" .
.;
assert +:= _erg = "vier";

_erg := vergleiche 2 mit
    fall 2 : "zwei" .
    fall 2 : "doppelt" .
    fall _ : "sonst" .
.;
assert +:= _erg = "zwei";

_erg := vergleiche [1, 2, 3] mit
    fall [1, 2, 3] : "korrekt" .
    fall [1, 2, c] : "drei-elementig" .
    fall [1, b, c] : "drei-elementig" .
    fall [1, 2]    : "zwei-elementig" .
    fall _         : "keine Ahnung" .
.;
assert +:= _erg = "korrekt";

Person := struct { name := "Alice", alter := 30 };
_erg := vergleiche Person mit
    fall struct { name := "Alice", alter := 30 } : "match" .
    fall _ : "nomatch" .
.;
assert +:= _erg = "match";

_erg := vergleiche 99 mit
    fall 1 : "eins" .
    fall 2 : "zwei" .
.;
assert +:= _erg = leere;
assert = 8
}
