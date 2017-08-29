#!/bin/bash

# Get Files entries from a given .changes or .dsc file
get_files()
{
    file=$(readlink -fn $1)
    echo $(awk '/^Files:/,EOF' $file | gawk '/^ [a-z0-9]{32} / {print $5}')
}

# Get Distribution entry from a given .changes or .dsc file
get_distribution()
{
    file=$(readlink -fn $1)
    echo $(awk '/^Distribution:/ {print $2}' $file)
}

# Get Architecture entry from a given .changes or .dsc file
get_architecture()
{
    file=$(readlink -fn $1)
    echo $(awk '/^Architecture:/ {print $2}' $file)
}

# Extract Debian codename and YunoHost distribution if present.
# It should be something like wheezy-stable
extract_codename_distribution()
{
    if [[ $1 = *-* ]]; then
	    [[ $1 = "old-stable" ]] && return 0

        i=0
        for p in `echo "$1" | tr "-" "\n"`; do
          case $i in
              0)
                if [[ $p =~ ^wheezy|jessie$ ]]; then
                    CODENAME=$p
                else
                    echo "invalid Debian codename $p"
                    return 1
                fi
                ;;
              1)
                if [[ $p =~ ^stable|testing|unstable$ ]]; then
                    DISTRIBUTION=$p
                else
                    echo "invalid distribution $p"
                    return 2
                fi
                ;;
              *)
                echo "unexpected string '$p' (i=$i)"
                return 3
          esac
          i=`expr $i + 1`
        done
    elif ! [[ $1 =~ ^stable|testing|unstable$ ]]; then
        echo "invalid distribution '$1'"
        return 4
    fi
}
