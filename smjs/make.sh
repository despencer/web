#!/bin/sh

SM_INCLUDE=mozjs-102
SM_LIBRARY=mozjs-102
PYTHON_INCLUDE=/usr/include/python3.12
WARNINGS="-Wno-invalid-offsetof -Wno-maybe-uninitialized"

gcc -I/usr/include/$SM_INCLUDE -I$PYTHON_INCLUDE -fPIC -Wall -std=c++2a -Werror $WARNINGS -shared -Wl,-soname,smjs.so -o smjs.so smjspython.cpp smjsvalues.cpp smjs.cpp -l$SM_LIBRARY