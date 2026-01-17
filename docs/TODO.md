Spilling und Datentypen

Rede von Thompson für den Turing Award hören

FIX: test/small_tests
test_even_odd      -> symtable idx falsch | hull reg des letrec ändert sich nicht bei gegenseitiger funktionsaufrufe
test_let5          -> spilling
test_live          -> symtable idx falsch       -> geht jetzt
test_ack           -> Optimierung (Spilling) | save callee-register -> geht jetzt wegen optimierung schon in zwischencode
test_lbd           -> Optimierung (Spilling) | save callee-register -> geht jetzt wegen optimierung schon in zwischencode

