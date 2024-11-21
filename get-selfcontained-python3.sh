#!/bin/bash

# https://github.com/indygreg/python-build-standalone/releases


OS_UPPERCASE=`uname -s | tr '[:lower:]' '[:upper:]' | sed 's/_.*$//'`
OS_LOWERCASE=`uname -s | tr '[:upper:]' '[:lower:]' | sed 's/_.*$//'`

selfcon_ext=selfcontained-python3
installed_dir=${selfcon_ext}/${OS_LOWERCASE}-64bit

echo ""
if [ ! -d $selfcon_ext ] ; then
    echo "Checking out from svn: Greenstone3's $selfcon_ext extension"
    svn co https://svn.greenstone.org/gs3-extensions/$selfcon_ext/trunk $selfcon_ext

    if [ $? != 0 ] ; then
	echo "Error encountered checking out: " 1>&2
	echo "    svn co https://svn.greenstone.org/gs3-extensions/$selfcon_ext/trunk $selfcon_ext" 1>&2
	exit 1
    fi
else
    echo "Detected directory '$selfcon_ext'"
    echo "=> Taken to mean that the svn check-out command has already been run"
fi

echo ""
if [ ! -d $installed_dir ] ; then
    echo "Runing the $selfcon_ext/PREPARE-${OS_UPPERCASE}.sh"

    cd $selfcon_ext && ./PREPARE-${OS_UPPERCASE}.sh

    if [ $? != 0 ] ; then
	echo "Error encountered running: " 1>&2
	echo "        cd $selfcon_ext && ./PREPARE-${OS_UPPERCASE}.sh" 1>&2
	exit 1
    fi
	
else
    echo "Detected directory '$installed_dir'"
    echo "=> Taken to mean that the $selfcon_ext/PREPARE-${OS_UPPERCASE}.sh command has already been run"    
fi


if [ "x$PYTHON3_HOME" != "x$PWD/$installed_dir" ] ; then
    echo ""
    echo "To use this installed version of Python3, in the top-level Greenstone3 directory run:"
    echo "    source ./gs3-setup-cli.sh"
    echo ""
else
    echo ""
    echo "Detected PYTHON3_HOME set to \$PWD/$installed_dir"
    echo "=> Taken to mean that the $selfcon_ext SETUP.sh file has been sourced"
fi

echo ""
