{
# Für die ganzen Mathe Definitionen. #
# Arithmetik, Konstanten #

# KONSTANTEN #
PI := 3.1415926535;
EXP := 2.718281828;
PHI := 1.61803398874;

# ABS #
abs := lambda x -> wenn x < 0 gilt, -x sonst x .;

# POWER #
pow := lambda (x, n) -> x**n;

# SQRT #
# Heron-Verfahren #
sqrt := lambda input ->
    {
        a := input;
        b := 1.0;
        solange (abs(a - b) > 1 e -6 ) gilt,
            a := input / b;
            b := (a+b) / 2;
        .;
        a;
    }
.;

# STACK #

}
