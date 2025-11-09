{
# LISTEN #
[]i64 lst := (1,2,3);
i64 assert := lst = (1 & (2 & (3 & leere)));

i64 sum := 0;
lst := 1 & (2 & (3 & leere));
für x in lst wiederhole
    sum := sum + x .;
assert +:= sum = 6;

[]i64 a := 1 & leere;
[]i64 b := 2 & a;
[]i64 c := 3 & b;
assert +:= c = 3 & (2 & (1 & leere));
assert = 3
}
