#!/bin/bash
set -e;

directory=/nfs/claudio/CASP12;
modelsuffix=server_models.stage2/pcons.in;
qasuffix=server_models.stage2/pcomb.full;
output=/nfs/robban/CASP12/claudio_01_stage2;
domains=domains.def;

for TARGETDIR in `find ${directory}/ -maxdepth 1 -type d -regex ".*/T[0-9]+"`;do
	skip=0;
	outputdir=${output}/`awk -F / '{print $NF}' <<< ${TARGETDIR}`;
	models=${TARGETDIR}/${modelsuffix};
	qa=${TARGETDIR}/${qasuffix};
	
	# Check so that this is a target ready for partitioning
	for checkfile in ${models} ${qa}; do
		if [ ! -e ${checkfile} ]; then
			#echo ${TARGETDIR} lacks ${checkfile};
			skip=1;
		fi;
	done;

	# Check so that its not already done
	if [ -e ${outputdir}/domains.def ]; then
		skip=2;
	fi;

	# Complain if done or not eligable and skip it
	case ${skip} in
		1)
			echo SKIPPING.... ${TARGETDIR};
			continue;
			;;
		2)
			echo DONE........ ${TARGETDIR};
			continue;
	esac;

	# Partition it otherwise
	echo "PARTITIONING ${TARGETDIR} -> ${outputdir}";
	cat ${models} | xargs casp12_partition.sh spectral_domain_partition_filtering ${outputdir} ${qa} sum 1>/dev/null 2>/dev/null;
done;
