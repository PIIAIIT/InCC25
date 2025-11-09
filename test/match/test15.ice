{
# ARITHMETIC ENTSCHEIDER #
sei (str, i64...) -> (str, i64...) arith := lambda (str, i64...) exp -> (str, i64...) {
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
}
in 
{
# TEST arith #
assert := arith(('+', ('+', 3, 2), 6)) = 5+6;
assert +:= arith(('-', 5, 6)) = 5-6;
assert +:= arith(('/', 5, 6)) = 5/6;
assert +:= arith(('^', 5, 6)) = 5**6;
assert +:= arith(('-', 5)) = -5;
assert +:= arith(('+', 5)) = +5;
assert +:= arith(('--', 5)) = ('--', 5);

assert = 7
}.
}
