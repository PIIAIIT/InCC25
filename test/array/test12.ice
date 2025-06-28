{
# LISTEN #
lst := (1,2,3);
assert := lst = (1 & (2 & (3 & leere)));

sum := 0;
lst := 1 & (2 & (3 & leere));
für x in lst wiederhole
    sum := sum + x .;
assert +:= sum = 6;

a := 1 & leere;
b := 2 & a;
c := 3 & b;
assert +:= c = 3 & (2 & (1 & leere));
assert = 3
}
