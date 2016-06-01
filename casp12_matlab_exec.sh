#!/bin/bash
set -e;

if [ -z $1 ]; then
	echo "USAGE: $0 <matlab_executable> [<arg1> <arg2> [...]]";
	exit 1;
fi;

bindir=`dirname $0`/bin;
mfile=$1;
arguments=${@:2};
matlabdir=`which matlab | awk -F / '{for (i=1; i <= NF-2; i++) printf "/%s", $i;}'`;

${bindir}/run_${mfile}.sh ${matlabdir} ${arguments};
