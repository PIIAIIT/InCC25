
Folie 36-37

[]= 8*(2+i)
mov qword muss angegeben werden

# Wenn extern malloc verwendet wird
extern malloc
section .data
 type_i64 dq 'i64     ', 0

nasm -felf64 progam.s
gcc -z noexecstack -no-pie progam.o
