{
# === Benannter Lambda-Ausdruck === #
i64 -> i64 add := lambda (i64 x, i64 y) -> i64 : x + y;
x := add(2, 3); # Erwartet: 5 #
assert := x = 5;

# === Unbenannter Lambda-Ausdruck === #
i64 x := (lambda i64 x -> i64 : x * x)(4); # Erwartet: 16 #
assert +:= x = 16;

# === Keyword- und Positionsargumente === #
format := lambda (i64 a, i64 b, i64 c) -> f64 : +(a | b - (c:=2));
f64 x := format(1, 2, c: 3); # Erwartet: "a=1, b=2, c=2" #
assert +:= x = 1.5;

# === Oversupply (Mehr Argumente) === #
# Funktion mit variadischen Argumenten (z.B. letzte ist Rest) #
variadic := lambda (i64 x, i64 y, rest...) -> i64 : x + y + länge(rest);
x := variadic(1, 2, 3, 4); # Erwartet: 1 + 2 + 2 = 5 #
assert +:= x = 5;

# === Undersupply (Teilanwendung) === #
multiply := lambda (i64 x, i64 y) -> i64 : x * y;
double := multiply(2); # => lambda (y) -> 2 * y #
x := double(5); # Erwartet: 10 #
assert +:= x = 10;

# Weitere Teilanwendung mit benanntem Argument #
setY := multiply(y: 10); # => lambda (x) -> x * 10 #
x := setY(3); # Erwartet: 30 #
assert +:= x = 30;

# === Kombination: Benannt + Undersupply === #
fancy := lambda (i64 x, i64 y, i64 z) -> i64 : x + 10*y + 100*z;
part := fancy(y: 2, z: 3); # => lambda (x) -> x + 20 + 300 #
x := part(4); # Erwartet: 324 #
assert +:= x = 324;
assert = 7 # Erwartet 7 #
}
