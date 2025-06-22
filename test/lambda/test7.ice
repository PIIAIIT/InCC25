{
# LAMBDA TEST #
# AUCH MIT LETREC #

x := sei fac = lambda x -> wenn x = 0 gilt, 1 sonst x*fac(x-1) . 
in fac(5) .;
assert := x = 120;

x := sei x = lambda x -> x*x 
in x(4) .;
assert +:= x = 16;

assert
}
