{
# ARARYS #

a := [10, 20, 30];
assert := a[1] = 20;

assert +:= a[0+2] = 30;

a := [];
assert +:= a = [];

sum := 0;
a := [1,2,3,4];
für x in a wiederhole
    sum +:= x.;
assert +:= sum = 10;
assert = 4
}
