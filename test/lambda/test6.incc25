{
# === Benannter Lambda-Ausdruck === #
add := lambda (x, y) -> x + y;
x := add(2, 3); # Erwartet: 5 #
assert := x = 5;

# === Unbenannter Lambda-Ausdruck === #
x := (lambda x -> x * x)(4); # Erwartet: 16 #
assert +:= x = 16;

# === Keyword- und Positionsargumente === #
format := lambda (a, b, c) -> +(a | b - (c:=2));
x := format(1, 2, c: 3); # Erwartet: "a=1, b=2, c=2" #
assert +:= x = 1.5;

# === Oversupply (Mehr Argumente) === #
# Funktion mit variadischen Argumenten (z.B. letzte ist Rest) #
variadic := lambda (x, y, rest...) -> x + y; #+ länge(rest);#
x := variadic(1, 2, 3, 4); # Erwartet: 1 + 2 + 2 = 5 #
assert +:= x = 3;

# === Undersupply (Teilanwendung) === #
multiply := lambda (x, y) -> x * y;
double := multiply(2); # => lambda (y) -> 2 * y #
x := double(5); # Erwartet: 10 #
assert +:= x = 10;

# Weitere Teilanwendung mit benanntem Argument #
setY := multiply(y: 10); # => lambda (x) -> x * 10 #
x := setY(3); # Erwartet: 30 #
assert +:= x = 30;

# === Kombination: Benannt + Undersupply === #
fancy := lambda (x, y, z) -> x + 10*y + 100*z;
part := fancy(y: 2, z: 3); # => lambda (x) -> x + 20 + 300 #
x := part(4); # Erwartet: 324 #
assert +:= x = 324;
assert # Erwartet 7 #
}
