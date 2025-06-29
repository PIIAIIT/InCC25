{
# factorial function #
n:=20;
x:=1;
für i in [1..n] wiederhole
  x := x * i
.;
assert := x = 2432902008176640000;
assert = 1 # CHECK ALLES RICHTIG #
}
