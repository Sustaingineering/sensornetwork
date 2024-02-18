#!/bin/bash

bold=$(tput bold)
normal=$(tput sgr0)
white=$(tput setaf 7)
green=$(tput setaf 2)
red=$(tput setaf 1)

error() {
  local parent_lineno="$1"
  local message="$2"
  local code="${3:-1}"
  echo
  if [[ -n "$message" ]] ; then
    echo "${normal}${red}Error on line $parent_lineno"
    echo "${bold}${red}Build of ${bn} failed with code ${code} and message: ${message}"
  else
    echo "${normal}${red}Error on line $parent_lineno"
    echo "${bold}${red}Build of ${bn} failed with code ${code}"
  fi
  exit "${code}"
}
trap 'error $LINENO' ERR

for codefile in code_*.py; do
  if [ -f "$codefile" ]; then
    name=$(cut -c 6- <<< ${codefile%.*})
    builddir=build/$name
    
    # First, clean the build output directory
    printf "${white}Cleaning build for $name...${normal} "
    rm -rf "$builddir"
    mkdir $builddir
    echo ${green}Success${normal}
    
    # Now, include common and code files for the target board
    printf "${white}Packaging build for $name...${normal} "
    cp -r common/* "$builddir" # Every file gets packaged
    cp "$codefile" "$builddir/code.py" # Only the relevant code file is included
    echo ${green}Success${normal}
    
    echo "${white}Searching libraries for $name:${normal}"
    mkdir "$builddir/lib"
    for libpath in libraries/*; do
      libname=$(basename "$libpath")
      
      # The operational library code is stored in a file/directory with the
      # same name as the parent directory, by Adafruit's convention
      printf "${white}Copying $libname...${normal} "
      cp -r "$libpath/$libname" "$builddir/lib"
      echo ${green}Success${normal}
    done
    
    echo "${white}${bold}Finished building $name!${normal}"
    
    # Make a new line
    echo
  fi
done

echo ${bold}${green}Build complete, no errors${normal}
