{
# Für die ganzen Mathe Definitionen. #
# Arithmetik, Konstanten #

# KONSTANTEN #
f64 PI  := 3.1415926535;
f64 EXP := 2.718281828;
f64 PHI := 1.61803398874;

# Fakultät #
# fac := lambda x ->
    wenn x > 0 gilt,
        fac(x-1) * x
    sonst
        1
    .
.; #

# Exponentialfunktion #
f64 exp := sei f64 eps = 60, ? fac = lambda f64 x -> 
    wenn x > 0 gilt,
      fac(x-1) * x
    sonst
      1
    .
in
    lambda f64 x -> {
        f64 sum := 0;
        für n in [0..eps] wiederhole
            sum +:= x**n | fac(n)
        .;
        sum
    }
.;

# ABS #
abs := lambda f64 x -> +x;

# SQRT #
# Heron-Verfahren #
sqrt := lambda f64 x -> {
  f64 a := x;
  f64 b := 1.0;
  solange (abs(a - b) > 1.0 e -6.0) gilt, {
    a := x | b;
    b := (a + b) | 2
  }.;
  a
};

# LOGARITHMUS #
f64 log := sei f64 prec = 60 in lambda f64 x -> {
  wenn x <= 0 gilt,
    echo("log of a non-positive number doesnt exist.")
  sonst {
    f64 sum := 0;
    für n in [0..prec] wiederhole
        sum +:= ((x-1)|(x+1))**(2*n+1) | (2*n+1)
    .;
    2.0 * sum
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
