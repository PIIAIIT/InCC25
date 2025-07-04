{
P := struct { x := 42 };
assert := P->x = 42;

P := struct { x:= 10; y:=20};
assert +:= P->x + P->y = 30;

P := struct { inner:= struct { val:= 99} };
assert +:= P->inner->val = 99;

add1 := lambda (s) -> s->x + 1;
P := struct { x:= 5};
assert +:= add1(P) = 6;

list := [struct { a:= 1 }, struct { a := 2 }];
assert +:= list[0]->a + list[1]->a = 3;

P := struct {square := lambda(x) -> x * x};
assert +:= P->square(4) = 16;
assert = 6 # Erwartet 6 #
}
