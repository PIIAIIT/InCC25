sei i64 res := 0 in {
# Beispiel 1 #
  res +:= sei str string := "Hello"
  in {
    sei str string2 := "World" 
    in
      string[4] = string2[1]
    .;
    sei str string := "Welt", str c := "W"
    in
      string[0] = c[0]
    .;
  }.;
# Beispiel 2 #
  res +:= sei str s := "ABCDE"
  in {
    sei str t := "abcde"
    in {
      sei str u := "12345"
      in {
        s[2] = t[2];
        t[4] = u[4]
      }.;
    }.;
  }.;
# Beispiel 3 #
# res +:= sei str wort := "Test", ()->str func := lambda -> str: "Halle"
  in
    func()[4] = wort[1]
  .;#
}.
