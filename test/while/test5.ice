{
i := 0;
sum := 0;
solange i < 5 gilt, {
    sum +:= i;
    i := i + 1;
}.;
assert := sum = 10;

i := 0;
x := 1;
solange x gilt, {
    i := i + 1;
    wenn i >= 3 gilt,
        x := 0
    .
}.;
assert +:= i = 3;

i := 10;
solange (i < 5) gilt, {
    echo(i);
    i := i + 1
}.;
assert +:= i = 10;

i := 0;
x := 0;
solange (i < 3) gilt, {
    j := 0;
    solange (j < 2) gilt, {
        x +:= i * 10 + j;
        # echo(x); #
        j := j + 1;
    }.;
    i := i + 1;
}.;
assert +:= x = 63;
assert = 4 # Erwartet 4 #
}
