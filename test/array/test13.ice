{
# ITERATOREN #
sum := 0;
für i in [1..5] wiederhole
    sum := sum + i .;
assert := sum = 15;

result := [];
für i in [1..5[ wiederhole
    result := result & [i] .;
assert +:= result = [1,2,3,4];

x := 0;
für i in [5..5[ wiederhole
    x := x + 1 .;
assert +:= x = 0;

result := [];
für i in [0..2+1] wiederhole
    result := result & [i] .;
assert +:= result = [0,1,2,3];
assert = 4
}
