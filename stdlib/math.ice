math := struct {
# Für die ganzen Mathe Definitionen. #
# Arithmetik, Konstanten #

# KONSTANTEN #
PI  := 3.1415926535;
EXP := 2.718281828;
PHI := 1.61803398874;

# Fakultät #
fac := lambda x ->
    wenn x > 0 gilt,
        fac(x-1) * x
    sonst
        1
    .
;

# Exponentialfunktion #
exp := sei eps = 60 in
    lambda x -> {
        sum := 0;
        für n in [0..eps] wiederhole
            sum +:= x**n | fac(n)
        .;
        sum
    }
.;

# ABS #
abs := lambda x -> wenn x < 0 gilt, -x sonst x .;

# SQRT #
# Heron-Verfahren #
sqrt := lambda x -> {
    a := x;
    b := 1.0;
    solange (abs(a - b) > 1 e -6 ) gilt, {
        a := x | b;
        b := (a + b) | 2
    }.;
    a
}
}
