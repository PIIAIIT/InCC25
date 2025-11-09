{
# LAMBDA TEST #
# AUCH MIT LETREC #

i64 x := sei i64 -> i64 fac := lambda i64 x -> i64 : wenn x = 0 gilt, 1 sonst x*fac(x-1) .
in fac(5) .;
assert := x = 120;

i64 x := sei i64->i64 x := lambda i64 x -> i64 : x*x
in x(4) .;
assert +:= x = 16;

i64 🗅:= sei i64->i64 x := lambda i64 a -> i64 : {
    wenn a = 0 gilt,
        1
    sonst
        a * y(a)
    .;
}, i64->i64 y := lambda i64 b -> i64 : {
    wenn b > 1 gilt,
        1/b * x(b-1)
    sonst
        b * x(b-1)
    .;
} in x(17) + y(7) .;
assert +:= 🗅= 355687428096720;
assert = 3
}
