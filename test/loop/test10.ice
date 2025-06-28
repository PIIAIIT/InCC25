{
# TEST LOOP STATEMENTS #
# SUMMIERUNG FUNCTION #
result := 0;
für i in [1, 2, 3, 4] wiederhole
    result := result + i .;
assert := result = 10;

# EMPTY ARRAY #
result := 42;
für x in [] wiederhole
    result := 0 .;
assert +:= result = 42;

# VERSCHACHTELT #
result := [];
für x in [1, 2] wiederhole
    für y in [3, 4] wiederhole
        result := result & [(x * y)] . .;
assert +:= result = [3, 4, 6, 8];

# SCHLEIFENVAR WIRD ÜBERSCHRIEBEN #
i := 100;
result := [];
für i in [1, 2, 3] wiederhole
    result := result & [i] .;
assert +:= result = [1,2,3];
assert +:= i = 100;

# ZUGRIFF AUF SCHLEIFENVAR IN AUSDRUCK #
result := 0;
für i in [1, 2, 3] wiederhole {
    i := i * 2;
    result := result + i
}.;
assert +:= result = 12;

x := 0;
für i in [1, 2, 3] wiederhole
    {} .;
assert +:= x = 0;
assert = 7 # ERWARTET 7 #
}
