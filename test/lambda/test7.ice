{
# LAMBDA TEST #
# AUCH MIT LETREC #

i64 x := sei fac := lambda i64 x -> wenn x = 0 gilt, 1 sonst x*fac(x-1) .
in fac(5) .;
assert := x = 120;

i64 x := sei x := lambda i64 x -> x*x
in x(4) .;
assert +:= x = 16;

i64 🗅:= sei x := lambda i64 a -> {
    wenn a = 0 gilt,
        1
    sonst
        a * y(a)
    .;
}, y := lambda i64 b -> {
    wenn b > 1 gilt,
        1/b * x(b-1)
    sonst
        b * x(b-1)
    .;
} in x(17) + y(7) .;
assert +:= 🗅= 355687428096720;
assert = 3
}
