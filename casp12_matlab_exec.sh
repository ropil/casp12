#!/bin/bash
set -e;

if [ -z $1 ]; then
	echo "USAGE: $0 <matlab_executable> [<arg1> <arg2> [...]]";
	exit 1;
fi;

bindir=`dirname $0`/bin;
mfile=$1;
arguments=${@:2};

${bindir}/run_${mfile}.sh ${arguments};
