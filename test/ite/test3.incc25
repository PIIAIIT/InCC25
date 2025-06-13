{
# TEST IF STATEMENTS #
x1 := 0;
wenn not x1 gilt,
  x1:=5
.;
assert := x1 = 5;

x2 := 1;
wenn not x2 gilt,
  x2:=0
sonst
  x2:=10
.;
assert +:= x2 = 10;

x3 := 10;
wenn x3 < x2 gilt,
  x3:=0
,aber wenn x3 = x2 gilt,
  x3:=5
sonst
  x3:=15
.;
assert +:= x3 = 5;


x4 := 10;
wenn (x4 < 5) gilt,
  x4:=0
,aber wenn (x4 < 7) gilt,
  x4:=5
,aber wenn (x4 = 9) gilt,
  x4:=10
sonst
  x4:=20
.;
assert +:= x4 = 20;

# Erwartet 4 #
assert
}
