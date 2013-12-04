#!/bin/bash

PRECISION=5
MOUNTPOINT=$1

generate_float()
{
	echo -n "0."
	for i in $(seq $PRECISION)
	do
		echo -n $(($RANDOM % 10))
	done
	echo
}

while [ $(cat $MOUNTPOINT/stock) -gt 0 ]
do
	x=$(generate_float)  
	y=$(generate_float)  
	echo "$x $y" > $MOUNTPOINT/pose_renfort
done

