# LAMBDA

- Benannter Lambda-Ausdruck:
  - f := lambda () -> expr;
- Unbenannter Lambda-Ausdruck:
  - Schlüsselwort lambda
  - lambda (args, args...) -> expr;
- Aufruf:
  - f(2, 3, b: 5)
  - Zuerst KeywordArgs {b} dann nicht namentliche args {2,3}\[0\]

# Parameter

- Mit Komma getrennte Argumentenliste und Oversupply of Arguments (x,y,z,c...)
- Oversupply wird explizit gemacht. Es muss deklaration angegeben werden.
-
- Funktion kann auch mit weniger Argumenten aufgerufen werden. f(y:5) ":=" \lambda x.
- Undersupply von Argumenten ist erlaubt f(5) ":=" \lambda y.
- Nachdem zu wenig Arugmente angegeben wurden gib es neue Closure zurück

# Builtin Funktion

- echo(x) (Print von x auf cout)
- länge(c) (Länge des Arrays `c`)

---

## **Lambda-Ausdrücke in unserer Sprache**

Lambda-Ausdrücke dienen zur Definition von anonymen oder benannten Funktionen. Sie sind eine zentrale Konstruktion zur funktionalen Programmierung innerhalb unserer Sprache und erlauben sowohl vollständige als auch teilweise Anwendung von Argumenten (Currying durch Unterversorgung).

### **1. Benannter Lambda-Ausdruck**

Ein benannter Lambda-Ausdruck wird mithilfe des Zuweisungsoperators `:=` einer Variable zugewiesen. Die Syntax ist:

```
f := lambda (arg1, arg2, ...) -> Ausdruck;
```

Beispiel:

```
add := lambda (x, y) -> x + y;
```

Dieser Ausdruck definiert eine Funktion `add`, die zwei Argumente entgegennimmt und deren Summe zurückgibt.

---

### **2. Unbenannter Lambda-Ausdruck**

Ein Lambda-Ausdruck kann auch anonym definiert werden, ohne ihn direkt einem Namen zuzuweisen. Dies geschieht durch einfaches Verwenden des `lambda`-Schlüsselworts:

```
lambda (arg1, arg2, ...) -> Ausdruck
```

Beispiel:

```
lambda (x) -> x * x
```

Dieser Ausdruck beschreibt eine Funktion, die das Quadrat ihres Arguments zurückgibt. Solche unbenannten Lambdas können direkt übergeben oder sofort aufgerufen werden.

---

### **3. Aufruf von Lambdas**

Der Aufruf erfolgt wie bei regulären Funktionen mit runden Klammern:

```
f(2, 3, b: 5)
```

Dabei gilt die folgende Regelung für die Übergabe von Argumenten:

- **Keyword-Argumente** (z. B. `b: 5`) werden zuerst verarbeitet.
- Danach folgen **nicht-benannte Argumente** (z. B. `2`, `3`), in ihrer Reihenfolge.

Das bedeutet: Die Argumenteliste wird aufgeteilt in benannte (nach Namen) und unbenannte Argumente (nach Position). Die Position der Argumente wird intern ab 0 indiziert.

---

## **Parameter und Argumentverhalten**

### **1. Argumentliste**

- Argumente werden in der Funktionsdefinition durch Kommata getrennt:

  ```
  lambda (x, y, z) -> ...
  ```

- Die Sprache erlaubt auch eine **Überversorgung** von Argumenten. Das bedeutet, beim Aufruf können mehr Argumente übergeben werden als formal definiert sind. In diesem Fall muss jedoch explizit in der Deklaration angegeben werden, wie mit den überschüssigen Argumenten umgegangen wird.

---

### **2. Unterversorgung (Partial Application)**

Die Sprache unterstützt **Teilapplikation** (Currying-artiges Verhalten):

- Wird eine Funktion mit **weniger Argumenten als erforderlich** aufgerufen, so wird **nicht sofort evaluiert**, sondern es wird **eine neue Closure zurückgegeben**, die auf die verbleibenden Argumente wartet.

Beispiel:

```
f := lambda (x, y) -> x + y;
g := f(5);         // g ist jetzt: lambda (y) -> 5 + y
echo(g(3));        // Ausgabe: 8
```

- Dieses Verhalten macht es möglich, Funktionen in Teilschritten zu verwenden oder sie gezielt in höherwertigen Funktionen weiterzugeben.

---

### **3. Benannte und optionale Argumente**

Lambda-Ausdrücke unterstützen benannte Argumente:

```
f := lambda (x, y) -> x * y;
f(y: 5) := lambda (x) -> x * 5;
```

In diesem Beispiel wurde `y` vorab mit `5` belegt, sodass die verbleibende Funktion nur noch `x` erwartet. Auch hier entsteht intern eine neue Closure mit den vorab gebundenen Werten.

---

## **Zusammenfassung**

Lambda-Ausdrücke in unserer Sprache ermöglichen flexible funktionale Konstrukte, einschließlich:

- Klarer Definition mit `lambda (...) -> ...`
- Unterstützung von benannten und unbenannten Argumenten
- Built-in Funktionen wie `echo` und `länge`
- Unter- und Überversorgung mit explizitem Verhalten
- Rückgabe neuer Closures bei unvollständiger Anwendung

Diese Gestaltung erlaubt eine präzise und dennoch flexible Nutzung von Funktionen und fördert den funktionalen Programmierstil in strukturierter Weise.

---

## **Builtin-Funktionen**

Die Sprache stellt einige eingebaute Funktionen zur Verfügung, darunter:

- `echo(x)`
  Gibt den Wert `x` auf `cout` (die Standardausgabe) aus.

- `länge(c)`
  Gibt die Länge des Arrays `c` zurück. Funktioniert für alle sequenziellen Datenstrukturen, die indiziert werden können.
