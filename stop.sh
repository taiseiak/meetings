#! /bin/bash
#
# Kill all current instances of flask_map on this machine
#
#

# Grep for all running processes containing flask_brevets in description
# EXCEPT the grep command itself; tgurn them into 'kill' commands and
# execute the commands with bash
#
ps -x | grep application | grep -v grep | \
    awk '{print "kill " $1}' | bash