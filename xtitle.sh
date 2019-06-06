#!/bin/bash
set -eu

title=$*
echo -e "\033]0;${title}\007"
