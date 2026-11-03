#!/bin/bash

#set -x
LC_ALL=C
export LC_ALL

# Driver name
drivername="TM/BA Series Printer Driver for Linux"
driverver="Ver.1.4.1"
package_name="tmt-cups-1.4.1.0"

# Interval (sec)
sleep_sec=0

## show version
##
version ()
{
	cat <<EOF
`basename $0`  for "${drivername}"  ${driverver}
  Copyright (C) 2010-2013 Seiko Epson Corporation. All rights reserved.

EOF
}

## show incompatible packages to be uninstalled
##
show_incompatible ()
{
if test "" != "$uninstall_packages" ; then
cat <<EOF
Before the installation, package:"${incmptbl_package}" must be uninstalled.
  Packages to be uninstalled:
    $incmptbl_tmcups
    $incmptbl_backend
EOF
if test "" != "$epuras" ; then
cat <<EOF2
    $epuras
EOF2
fi
cat <<EOF3

EOF3
fi
}

## show usage
##
usage ()
{
cat <<EOF
Driver package installer for "${drivername}"
  Target package: ${package_name}

usage: `basename $0` [option]

  option:
	-t | --test    Test mode          (do not install)
	-h | --help    Show help message  (do not install)
	-u | --usage   Show usage message (do not install)
	-v | --version Show version info  (do not install)

EOF
if test "$1" != "0" ; then
	show_incompatible
fi
}

## wait Enter key pressed
##
press_enter_key ()
{
	echo -n "Press the Enter key."
	read REPLY
}

## check command validity
##
check_command ()
{
    which "$1" 1>/dev/null 2>&1
}

#
# Prepare for installation
#
# check package management system.
default_packager=""
for cmd in rpm dpkg ; do
    check_command $cmd
    if test $? -eq 0 ; then
		default_packager=$cmd
    fi
done
if test -z ${default_packager} ; then
    echo "[ERROR] Fatal error."
    press_enter_key
    exit 255
fi

#
# Check installed package
#
# Uninstall target (incompatible version driver packages)
target_packages="
    tmt-cups
    tmu-cups-filter
    epson-cups-escpos
    ep-escpos
    ep-core
    ep-client
    tmx-cups
    tmx-cups-backend
"
# Control variables to be set here:
#	uninstaller			uninstall command
#	uninstall_packages	packages to be uninstalled
#	incmptbl_package	incompatible version package name to be uninstalled
#	incmptbl_tmcups		incompatible version filter package to be uninstalled
#	incmptbl_backend	incompatible version backend package to be uninstalled
#	epuras				old version epuras packages to be uninstalled
uninstaller=""
uninstall_packages=""
incmptbl_package="(unknown)"
incmptbl_tmcups="(filter package not found)"
incmptbl_backend="(backend package not found)"
epuras=""
for cmd in rpm dpkg ; do
    check_command $cmd
    if test $? -eq 0 ; then
		if test "rpm" = "$cmd" ; then
			option="-q"
		else
			option="-l"
		fi
		for package in ${target_packages} ; do
			if test "rpm" = "$cmd" ; then
				pkginfo=`$cmd ${option} ${package} 2>/dev/null`
			else
				pkginfo=`$cmd ${option} ${package} 2>/dev/null|grep ii`
			fi
			if test $? -eq 0 ; then
				uninstaller="$cmd"
				if test "rpm" = "$cmd" ; then
					# for rpm, pkginfo must be 'package-version' form
					pkg_ver="${pkginfo#$package?}"
				else
					# for dpkg, pkginfo must be 'ii package version description' form
					pkg_ver=`echo $pkginfo|cut -d " " -f 3`
				fi
				case "$package" in
					"tmt-cups" )
						# for tmt-cups, pkg_ver must be verified to be <= 1.0.x
						if test "1.0" = "${pkg_ver:0:3}" ; then
							incmptbl_tmcups="$package-$pkg_ver"
							uninstall_packages="$uninstall_packages
    $package"
						fi
						;;
					"tmu-cups-filter" )
						incmptbl_package="tmu-cups-1.0.0.0"
						incmptbl_tmcups="$package-$pkg_ver"
						uninstall_packages="$uninstall_packages
    $package"
						;;
					"epson-cups-escpos" )
						incmptbl_backend="$package-$pkg_ver"
						uninstall_packages="$uninstall_packages
    $package"
						;;
					ep-* )
						if test "(unknown)" = $incmptbl_package -a "ep-escpos" = "$package"; then
							case "$pkg_ver" in
								"2.3.2.90-1" ) incmptbl_package="tmt-cups-1.3.x.0" ;;
								"2.3.0.90-1" ) incmptbl_package="tmt-cups-1.2.1.0" ;;
								"2.0.10.6-1" | "2.0.10.5-1" ) incmptbl_package="tmt-cups-1.2.0.0" ;;
								"2.0.10.101-1" ) incmptbl_package="tmt-cups-1.1.0.1" ;;
								"2.0.10.2-1" ) incmptbl_package="tmt-cups-1.1.0.0" ;;
								"2.0.10.0-1" ) incmptbl_package="tmt-cups-1.0.x.0" ;;
							esac
						fi
						if test "" != "$epuras" ; then
							epuras="$epuras
    "
						fi
						epuras="$epuras$package-$pkg_ver"
						uninstall_packages="$uninstall_packages
    $package"
						;;
					"tmx-cups" )
						incmptbl_tmcups="$package-$pkg_ver"
						uninstall_packages="$uninstall_packages
    $package"
						;;
					"tmx-cups-backend" )
						case "$pkg_ver" in
							"1.1.1.0-1" ) incmptbl_package="tmx-cups-1.4.50.0" ;;
							* ) incmptbl_package="tmx-cups-1.4.x.0" ;;
						esac
						incmptbl_backend="$package-$pkg_ver"
						uninstall_packages="$uninstall_packages
    $package"
						;;
					* ) ;;
				esac
			fi
		done
		test "" != "$uninstaller" && break
    fi
done
if test -z $uninstaller ; then
    uninstaller=${default_packager}
fi

#
# execute simple optional action, setting TEST option flag
#
TEST="no"
for a in $* ; do
	case "$a" in
		"-t" | "--test"    ) TEST="yes" ;;
		"-h" | "--help"    ) version ; usage ; exit 0 ;;
		"-u" | "--usage"   )           usage 0 ; exit 0 ;;
		"-v" | "--version" ) version ;         exit 0 ;;
		"--"               ) break ;;
		*) echo "[ERROR] Unknown option."; exit 255 ;;
	esac
done

# Change root.
if [ 0 -ne `id -u` ] ; then
	echo "Running the sudo command..."
	sudo $0 $*
	status=$?
	if [ 1 -eq ${status} ] ; then
		echo ""
		echo "[ERROR] The sudo command failed."
		echo "[ERROR] Please execute the `basename $0` again after changing to the root."
		press_enter_key
	fi
	exit ${status}
fi

# show version at first.
version

#
# Uninstall incompatible TM/BA printer driver installation, if detected
#
if test "" != "$uninstall_packages" ; then
	echo "Incompatible version of TM/BA printer driver found!"
	show_incompatible

	# Get CUPS printers that use the driver to be uninstalled.
	# set locale = en_US to unify output string format
	LANG_O=${LANG}
	LANG="en_US.utf8"
	if test "" != "$epuras" ; then
		uripfx="epsontm:/ESDPRT"
	else
		uripfx="tmbaprn:/ESDPRT"
	fi
	# get the line including $uripfx from lpstat output.
	# and get the 3rd word from the line, setting it to tmprnlist
	tmprnlist=`lpstat -t 2>/dev/null|grep "$uripfx"|cut -d " " -f 3`
	# recover locale
	LANG=${LANG_O}

	# set uninstaller option.
	if test "rpm" = "${uninstaller}" ; then
		if test "no" = "${TEST}" ; then
		    option="-e"
		else
		    option="-e --test"
		fi
	else
		if test "no" = "${TEST}" ; then
		    option="-P"
		else
		    option="--no-act -P"
		fi
	fi

	if test "no" = "${TEST}" ; then
		# user confirm: uninstalling the incompatible printer driver installation
		while true ; do
			echo -n "Uninstall the incompatible printer driver: ${incmptbl_package}  [y/n]? "
			read a
			answer="`echo $a | tr A-Z a-z`"
			case "$answer" in
				"y" | "yes" ) break ;;
				"n" | "no"  )
					echo "Uninstallation canceled."
					echo ""
					echo "You can't install new TM/BA series printer driver without uninstalling "
					echo "the incompatible version."
					press_enter_key
					exit 0 ;;
				* ) echo "[ERROR] Please enter \"y\" or \"n\"." ;;
			esac
		done

		# Do uninstall.
		if test -f /var/epson/epuras/epuras.properties ; then
			if test -f /tmp/epuras.properties ; then
				echo "Move /tmp/epuras.properties to /tmp/epuras.properties.bak"
				mv /tmp/epuras.properties /tmp/epuras.properties.bak
			fi
			echo "Backup /var/epson/epuras/epuras.properties to /tmp/..."
			cp -p /var/epson/epuras/epuras.properties /tmp/ 
		fi
		for package in ${uninstall_packages} ; do
			echo "${uninstaller} ${option} ${package}"
			${uninstaller} ${option} ${package}
			sleep ${sleep_sec}
		done
		echo ""

		# preset yes
		answer="y"
		if test "" != "$tmprnlist" ; then
			# user confirm: deleting printers that use the uninstalled TM/BA series printer driver
			while true ; do
				echo -n "Delete printers that use the driver you have uninstalled ahead [y/n]? "
				read a
				answer="`echo $a | tr A-Z a-z`"
				case "$answer" in
					"y" | "yes" ) break ;;
					"n" | "no"  ) answer="n"; break ;;
					*         ) echo "[ERROR] Please enter \"y\" or \"n\"." ;;
				esac
			done
		fi

	else
		# Do uninstall test.
		echo "* default_packager=${default_packager}"
		echo "* uninstaller=${uninstaller} ${option}"
		echo "* packages to be uninstalled: ${uninstall_packages}"
		echo "* Uninstall test:"
		${uninstaller} ${option} ${uninstall_packages}
		if test "" != "$tmprnlist" ; then
			# Show recommendation message
			echo "Desirable to delete the printers that use the incompatible driver."
		fi
		# force to yes on test mode.
		answer="y"
	fi

	if test "y" = "${answer}" ; then
		# Delete CUPS printers that use the uninstalled driver.
		# delete all printers in tmprnlist
		if test "" != "$tmprnlist" ; then
			for tmprn in $tmprnlist ; do
				# remove the last ':'
				tmprn=${tmprn%:}
				# delete tmprn
				if test "no" = "${TEST}" ; then
					echo "Deleting printer: $tmprn"
					lpadmin -x $tmprn
				else
					# only display message on test mode
					echo "  Desirable to delete the printer: $tmprn."
				fi
			done
		else
			echo "No printer using the incompatible driver."
		fi
	else
		# only display message when the printer deletion cancelled
		echo "Printer deletion canceled."
	fi
	echo ""
fi

#
# Start installation
#
# Set top directory.
programPath=`which $0`
topDir=`dirname "$programPath"`

## Subroutines
##

## Do distribution check. (return distName)
##
checkDistribution ()
{
	# check distribution
	checkdistName=`lsb_release -d 2>/dev/null`
	os=`echo "$checkdistName" | awk '{print $2}'`
	ver=`echo "$checkdistName" | awk '{print $3}'`
	p4=`echo "$checkdistName" | awk '{print $4}'`
	p5=`echo "$checkdistName" | awk '{print $5}'`
	if [ "xFedora" = x$os ]; then
		ver=$p4
	fi
	if [ "SUSE-Linux-Enterprise-Desktop" = $os-$ver-$p4-$p5 ]; then
		os="SLED"
		ver=`echo "$checkdistName" | awk '{print $6}'`
	fi
	if [ "x" = x$os ]; then
		cat /etc/*release | grep -q openSUSE > /dev/null 2>&1
		if [ 0 -eq $? ]; then
			os="openSUSE"
			ver=`cat /etc/*release | head -1 | awk '{print $2}'`
		else
			cat /etc/*release | grep -q _ID= | grep -q Ubuntu > /dev/null 2>&1
			if [ 0 -eq $? ]; then
				os="Ubuntu"
				ver=`cat /etc/*release | grep DISTRIB_RELEASE=`
				ver=${ver#DISTRIB_RELEASE=}
			else
				cat /etc/*release | head -1 | grep -q Fedora > /dev/null 2>&1
				if [ 0 -eq $? ]; then
					os="Fedora"
					ver=`cat /etc/*release | head -1 | awk '{print $3}'`
				else
					os="Unknown"
				fi
			fi
		fi
	fi
	distName=$os-$ver
}

## The Architecture is checked.  (return archName)
##
checkArchitecture () {
	#Select Architecte
	checkArchName=`uname -m`

	case "$checkArchName" in
		"i386" | "i486")
			archName="i386"
			;;
		"i586" | "i686")
			archName="i586"
			;;
		"amd64" | "x86_64")
			archName="x86_64"
			;;
		*)
			archName=""
			;;
	esac
}


## Packages installation ($1=PackageListFile)
##
packageInstall ()
{
	# Get list filename.
	list="$1"
	status=0

	[ "yes" = "$TEST" ] && echo "* Package list file = ${list}"

	if [ -f "${list}" ] ; then

		packageType=`basename ${list} | sed -e 's,\.list$,,' | awk -F- '{ print $4 }'`

		case "${packageType}" in
			"RPM")
				installCommand="rpm -U"
				[ "yes" = "$TEST" ] && installCommand="rpm -U --test"
				;;
			"DEB")
				installCommand="dpkg -i --no-force-downgrade"
				[ "yes" = "$TEST" ] && installCommand="dpkg --no-act -i --no-force-downgrade"
				;;
			*)
				echo "[ERROR] Fatal error."
				echo "[ERROR] Package installation failed."
				press_enter_key
				exit 255
				;;
		esac

		cd $topDir

		if [ "yes" = "${TEST}" ] ; then
			echo "* Target packages:"
			ls -1 `cat ${list}`
			echo "* Install test:"
			$installCommand `cat ${list}`
			status=0
		else
			for file in `cat ${list}` ; do
				$installCommand "$topDir/$file"
			done
			status=$?
		fi

	else
		echo "[ERROR] cannot access ${list}: No such file."
		echo "[ERROR] Package installation failed."
		press_enter_key
		exit 255
	fi
	return ${status}
}

## get splitted installation package list name (return splitListName)
##
get_splitListName ()
{
	list=`basename $1 | sed -e 's,\.list$,,'`

	dist=`echo ${list} | awk -F- '{ print $1 }' | sed -e 's,_, ,g'`
	rel=`echo ${list} | awk -F- '{ print $2 }'`
	arch=`echo ${list} | awk -F- '{ print $3 }'`
#	pkg=`echo ${list} | awk -F- '{ print $4 }'`

	case "$arch" in
		"i386" | "i486" | "i586" | "i686")
			displayArch="x86(32bit)"
			;;
		"amd64" | "x86_64")
			displayArch="x86_64(64bit)"
			;;
		*)
			displayArch="$arch"
			;;
	esac

	splitListName="${dist} ${rel} ${displayArch}"
}

## User select number (255 is error)
##
get_number ()
{
	read line

	n=`expr "${line}" \* 1 2>/dev/null`
	[ $? -ge 2 ] && return 255

	if [ $n -lt 0 ] ; then
		return 255
	fi

	return $n
}

## select distribution for manual install
##
select_list_file ()
{
	number=0
	endStrings=""

	while true ; do
		echo ""
		echo "Please select your distribution."

		endStrings="Select number [0(cancel)"

		count=0
		for list in `ls -1 $topDir/.install/*.list | LC_ALL=C sort` ; do

			get_splitListName "$list"

			count=`expr $count + 1`

			echo "$count.${splitListName}"

			endStrings="$endStrings/$count"

		done

		echo -n "${endStrings}]? "

		get_number
		number=$?

		if [ 0 -eq $number ] ; then
			echo "Installation canceled."
			press_enter_key
			exit 0
		fi

		if [ ${number} -le ${count} ] ; then

			i=0
			selectedListFile=""
			for list in `ls -1 $topDir/.install/*.list | LC_ALL=C sort` ; do

				i=`expr $i + 1`

				if [ ${number} -eq $i ] ; then
					selectedListFile="$list"
					break ;
				fi
			done

			if [ -n "${selectedListFile}" ] ; then
				break
			fi
		fi

		echo "[ERROR] Please input a correct number."
	done
}

#
# MAIN
#

#check Distribution.
distName=
checkDistribution
[ "yes" = "$TEST" ] && echo "* This distribution is \"${distName}\""

#check Architectur
archName=
checkArchitecture
[ "yes" = "$TEST" ] && echo "* Machine Architecture is \"${archName}\""

#get package list file name
targetFile=`ls -1 $topDir/.install/$distName-$archName-*.list 2> /dev/null`

if [ -n "$targetFile" -a -f "$targetFile" ] ; then

	while true ; do

		get_splitListName "${targetFile}"

		echo -n "Install ${package_name} into ${splitListName} [y/n]? "
		read a

		answer="`echo $a | tr A-Z a-z`"

		case "$answer" in
			"y" | "yes" )
				# take default action
				break
				;;
			"n" | "no"  )
			    # manual installation, selecting distribution
				select_list_file
				targetFile="${selectedListFile}"
				break
				;;
			* )
				echo "[ERROR] Please enter \"y\" or \"n\"."
				;;
		esac
	done
else
	select_list_file
	targetFile="${selectedListFile}"
fi

#Do Packages installation
packageInstall ${targetFile}

#Show finishing message and wait Enter Key
echo ""
if test "no" == "${TEST}" ; then
	echo "*** The installation finished. ***"
else
	echo "*** The installation test finished. ***"
fi
echo ""
press_enter_key

# end of file
