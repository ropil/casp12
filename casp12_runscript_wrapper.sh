#!/bin/bash
#
# Run the CASP12 domain partitioner on specified target directories
# Copyright (C) 2017  Robert Pilstål
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program. If not, see <http://www.gnu.org/licenses/>.
set -e;

# Number of settings options
NUMSETTINGS=1;
# If you require a target list, of minimum 1, otherwise NUMSETTINGS
let NUMREQUIRED=${NUMSETTINGS}+1;
# Start of list
let LISTSTART=${NUMSETTINGS}+1;

# I/O-check and help text
if [ $# -lt ${NUMREQUIRED} ]; then
  echo "USAGE: [ENV1=value] $0 <out_dir> <target_dir1> [<target_dir2> [...]]";
  echo "";
  echo " OPTIONS:";
  echo "  out_dir     - Directory where to save output";
  echo "  target_dirX - Directories wherein targets are found, as";
  echo "                subdirs";
  echo "";
  echo " ENVIRONMENT:";
  echo "  PARTITIONER - MATLAB partitioner function to use, out of;";
  mdir="`dirname $0`/matlab";
  for partitioner in `find ${mdir} -maxdepth 1 -regex '.*/spectral_domain_.*\.m'`; do
  echo "                `basename ${partitioner} .m`";
  done;
  echo "  ENV1 - description...               ... no longer than this!";
  echo "";
  echo " EXAMPLES:";
  echo "  # Run on three files, with ENV1=1";
  echo "  ENV1=1 $0 file1 file2 file3 > output.txt";
  echo "";
  echo "casp12_runscript_wrapper  Copyright (C) 2017  Robert Pilstål;"
  echo "This program comes with ABSOLUTELY NO WARRANTY.";
  echo "This is free software, and you are welcome to redistribute it";
  echo "under certain conditions; see supplied General Public License.";
  exit 0;
fi;

# Parse settings
output=$1;
targetlist=${@:$LISTSTART};

# Set default values
if [ -z ${MODELSUFFIX} ]; then
  MODELSUFFIX='.*_TS[[:digit:]]+\.pdb';
fi
if [ -z ${QASUFFIX} ]; then
  QASUFFIX="quality_assessment.pcs";
fi
if [ -z ${PARTITIONER} ]; then
  PARTITIONER="spectral_domain_partition_tensor_filtering_adjacency";
fi
if [ -z ${DOMAINSUFFIXj} ]; then
  DOMAINSUFFIX="domains.def";
fi

# Setup the paths
source ${HOME}/.worktool;
PATH=`dirname $0`:${PATH};

# Loop over arguments
for directory in ${targetlist}; do
  for TARGETDIR in `find ${directory}/ -maxdepth 1 -type d -regex ".*/T[0-9]+"`;do
    skip=0;
    outputdir=${output}/`awk -F / '{print $NF}' <<< ${TARGETDIR}`;
    regex="${TARGETDIR}/${MODELSUFFIX}";
    qa="${TARGETDIR}/${QASUFFIX}";
	
    # Check so that this is a target ready for partitioning
    for checkfile in ${qa}; do
      if [ ! -e ${checkfile} ]; then
        echo ${TARGETDIR} lacks ${checkfile};
        skip=1;
      fi;
    done;

    # Check so that its not already done
    if [ -e ${outputdir}/${DOMAINSUFFIX} ]; then
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
    find ${TARGETDIR} -maxdepth 1 -regextype egrep -regex ${regex} \
      | xargs casp12_partition.sh ${PARTITIONER} ${outputdir} ${qa} sum \
      1>/dev/null 2>/dev/null;
    # Draw the partition...
    DISPLAY= casp12_matlab_exec.sh draw_partition ${outputdir}/partition.dat ${outputdir}/partition.png 1>/dev/null 2>/dev/null;
  done;
done;
