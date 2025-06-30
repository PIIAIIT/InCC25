{
# LAMBDA TEST #
# AUCH MIT LETREC #

x := sei fac = lambda x -> wenn x = 0 gilt, 1 sonst x*fac(x-1) .
in fac(5) .;
assert := x = 120;

x := sei x = lambda x -> x*x
in x(4) .;
assert +:= x = 16;

🗅:= sei x = lambda a -> {
    wenn a = 0 gilt,
        1
    sonst
        a * y(a)
    .;
}, y = lambda b -> {
    wenn b > 1 gilt,
        1/b * x(b-1)
    sonst
        b * x(b-1)
    .;
} in x(17) + y(7) .;
assert +:= 🗅= 355687428096720;
assert = 3
}
