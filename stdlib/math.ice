{
# Für die ganzen Mathe Definitionen. #
# Arithmetik, Konstanten #

# KONSTANTEN #
PI  := 3.1415926535;
EXP := 2.718281828;
PHI := 1.61803398874;

# Fakultät #
# fac := lambda x ->
    wenn x > 0 gilt,
        fac(x-1) * x
    sonst
        1
    .
.; #

# Exponentialfunktion #
exp := sei eps = 60, fac = lambda x -> 
    wenn x > 0 gilt,
      fac(x-1) * x
    sonst
      1
    .
in
    lambda x -> {
        sum := 0;
        für n in [0..eps] wiederhole
            sum +:= x**n | fac(n)
        .;
        sum
    }
.;

# ABS #
abs := lambda x -> +x;

# SQRT #
# Heron-Verfahren #
sqrt := lambda x -> {
  a := x;
  b := 1.0;
  solange (abs(a - b) > 1 e -6) gilt, {
    a := x | b;
    b := (a + b) | 2
  }.;
  a
};

# LOGARITHMUS #
log := sei prec = 60 in lambda x -> {
  wenn x <= 0 gilt,
    echo("log of a non-positive number doesnt exist.")
  sonst {
    sum := 0;
    für n in [0..prec] wiederhole
        sum +:= ((x-1)|(x+1))**(2*n+1) | (2*n+1)
    .;
    2 * sum
  }.
}.;

# isPrim #
isPrim := lambda x -> {
  i := 2;
  prim := 1;
  solange i < x gilt, {
    t  := x mod i;
    wenn t = 0 gilt, {prim:=0; i:=x} .;
    i +:= 1;
  }.;
  wenn x <= 1 gilt, prim := 0 .;
  prim
}

}
