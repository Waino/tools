#!/usr/bin/env python3

# Copyright (c) 2019, Stig-Arne Grönroos.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# 
# 
# Usage:
#   Given a unique pattern matching the command line of a running command
#   (COMMAND column in *ps* output), tries to find the terminal in which that
#   command is running, and focus the terminal window.
# 
#   Useful if you have way too many terminals open.
# 
# Usage example:
#   findt.py a_file_open_in_some_editor

# Depends on xdotool package

from __future__ import unicode_literals

import collections
import subprocess
import sys

PsResult = collections.namedtuple('PsResult', ['pid', 'ppid', 'command'])

PS_PATTERN_FORMAT = 'ps -eo pid,ppid,args | grep {} | grep -v grep | grep -v findt'
PS_PID_FORMAT = 'ps -o pid,ppid,args {}'
MAX_RECURSION = 8
DEFAULT_TERM = 'rxvt'

def pattern_to_pid(pattern):
    try:
        out = subprocess.check_output(
            PS_PATTERN_FORMAT.format(pattern),
            shell=True).decode()
        return PsResult(*out.strip().split(None, 2))
    except Exception as e:
        print('Cannot find process with pattern "{}"'.format(pattern))
        raise e


def expand_pid(pid):
    try:
        out = subprocess.check_output(
            PS_PID_FORMAT.format(pid),
            shell=True).decode()
        out = out.strip().split('\n')[-1]
        return PsResult(*out.strip().split(None, 2))
    except Exception as e:
        print('Cannot find parent process using pid "{}"'.format(pid))
        raise e
        

def parent_terminal(result, term):
    for _ in range(MAX_RECURSION):
        if result.command.startswith(term):
            return result
        if result.ppid == '1' or result.ppid == '0':
            raise Exception(
                'Cannot find parent terminal. ' +
                'Are you sure you are using "{}"'.format(term))
        result = expand_pid(result.ppid)
    raise Exception(
            'Recursion limit reached searching for parent terminal.')
    

def activate_by_pid(pid, term):
    try:
        subprocess.check_call(
            ['xdotool', 'search', '--all', '--pid', str(pid),
             '--class', str(term), 'windowactivate'])
    except Exception as e:
        print('Unable to activate window')
        raise e


def main(argv):
    if len(argv) < 1:
        print('Usage: {} pattern [term]'.format(sys.argv[0]))
        sys.exit(1)
    if len(argv) == 2:
        term = argv[1]
    else:
        term = DEFAULT_TERM
    try:
        pid = expand_pid(int(argv[0]))
    except ValueError:
        pid = pattern_to_pid(argv[0])
    result = parent_terminal(
        pid, term)
    activate_by_pid(result.pid, term)

if __name__ == "__main__":
        main(sys.argv[1:])

