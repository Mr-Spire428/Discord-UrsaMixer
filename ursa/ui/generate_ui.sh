#!/bin/bash

FLAGS="$1"
for i in *.ui; do
	pyuic5 $FLAGS -o ${i/.ui/.py} ${i}
done
