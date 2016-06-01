#!/bin/bash

mcc=mcc
exedir=`dirname $0`;
matdir=${exedir}/matlab;
bindir=${exedir}/bin;

mkdir -p ${bindir};

for m in `find ${matdir}/ -maxdepth 1 -type f -regex ".*\.m"`; do
	echo "${mcc} -m ${m} -d ${bindir} -o `basename ${m} .m`";
	${mcc} -m ${m} -d ${bindir} -o `basename ${m} .m`;
done;
