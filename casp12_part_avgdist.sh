#!/bin/bash
set -e;

if [ -z $4 ]; then
	echo "USAGE: $0 <partitioner> <DIR> <QA> <PDB>[ <PDB>[...]]";
	echo "";
	echo "  partitioner - script to use for partitioning (executable)";
	echo "  DIR - output directory where all results are spammed";
	echo "  QA - path to quality assesment file to use";
	echo "  PDB - model files, at least one";
	exit 1;
fi

PART=$1
DIR=$2;
QA=$3;
MODELS=${@:4};

ORDERFILE=${DIR}/model_order.dat;
DOMAINFILE=${DIR}/domains.def;
ATOMFILE=${DIR}/atoms.dat;
LENGTHFILE=${DIR}/length.dat;
DOMINANTFILE=${DIR}/dominant.dat;
MODELDIR=${DIR}/selected;
TENSOR=${DIR}/tensor.dat;
RAWQA=${DIR}/qa_raw.dat;
SORTEDQA=${DIR}/qa_sort.dat;
VECTORQA=${DIR}/qa_vector.dat;

mkdir -p ${DIR};

# Here we should echo all the settings into a settings.dat ...

# Descide which length that is dominant
#######################################
# Get model vs number of atoms
grep -c ^ATOM.*CA.* ${MODELS} > ${ATOMFILE};
# Get a file of all length's
awk -F : '{print $2}' ${ATOMFILE} > ${LENGTHFILE};
rm -f ${DOMINANTFILE};
# For each unique length, count it's occurences
for i in `sort -u ${LENGTHFILE}`; do
	echo ${i} `grep -c ^${i}$ ${LENGTHFILE}` >> ${DOMINANTFILE};
done;
dominant=`sort -nrk 2 ${DOMINANTFILE} | head -n 1 | awk '{print $1}'`;

# Copy the dominant files
#########################
mkdir -p ${MODELDIR};
for pdb in `awk -F : -v num=${dominant} '
{
  if($2 == num)
    print $1;
}' ${ATOMFILE};`; do
  grep ^ATOM.*CA.* ${pdb} > ${MODELDIR}/`basename ${pdb}`;
done;

# Extract the distance tensor
#############################
# Define the order of the tensor (important; will sync the weights with the
# tensor)
find ${MODELDIR}/ -type f > ${ORDERFILE};
# Extract the distance tensor
cat ${ORDERFILE} | xargs casp12_pdb_tensor.py > ${TENSOR};

# Extract the QA weight vector
##############################
## This first step might not be needed... since we are greping things out anyway
#grep "^\S\+\s\+[[:digit:]]\+\.[[:digit:]]\+" ${QA} \
	#| awk '{print $1, $2}' > ${RAWQA};
rm -f ${SORTEDQA};
for server in `awk -F / '{print $NF}' ${ORDERFILE}`; do
	grep "^${server}\s\+[[:digit:]]\+\.[[:digit:]]\+" ${QA} >> ${SORTEDQA};
done;
awk '{print $2}' ${SORTEDQA} > ${VECTORQA};
