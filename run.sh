#!/bin/bash

if [ ! -d ~/.gremlin ];then
	mkdir ~/.gremlin
fi

export ARG=$1
RELATIVEDIR=`echo $0|sed s/run.sh//g`
cd $RELATIVEDIR
chmod +x ./src/main.py &> 'log.txt'
python3 -u ./src/main.py $ARG &>> 'log.txt' 

