{
# ARITHMETIC ENTSCHEIDER #
arith := lambda exp -> {
    vergleiche exp mit
        fall ('+', a, b) : arith(a) + arith(b) .
        fall ('-', a, b) : arith(a) - arith(b) .
        fall ('*', a, b) : arith(a) * arith(b) .
        fall ('/', a, b) : arith(a) / arith(b) .
        fall ('^', a, b) : arith(a) ** arith(b) .
        fall ('-', a) : -arith(a) .
        fall ('+', a) : +arith(a) .
        fall _ : exp .
    .
}.;

# TEST arith #
assert := arith(('+', 5, 6)) = 5+6;
echo(assert);
assert +:= arith(('-', 5, 6)) = 5-6;
echo(assert);
assert +:= arith(('/', 5, 6)) = 5/6;
echo(assert);
assert +:= arith(('^', 5, 6)) = 5**6;
echo(assert);
assert +:= arith(('-', 5)) = -5;
echo(assert);
assert +:= arith(('+', 5)) = +5;
echo(assert);
assert +:= arith(('--', 5)) = ('--', 5);
echo(assert);

assert = 7
}
