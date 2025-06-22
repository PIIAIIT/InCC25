{
# FizzBuzz ohne print #
y:=0;
n:=10;
für i in ]0..n] wiederhole
  wenn (i mod 3 = 0 and i mod 5 = 0) gilt,
    y +:= 15
  ,aber wenn (i mod 3 = 0) gilt,
    y +:= 3
  ,aber wenn (i mod 5 = 0) gilt,
    y +:= 5
  sonst
    y +:= 1
  .
.;
y;
assert := y = 24;
assert;
}
