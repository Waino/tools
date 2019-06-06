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
#   Tries to reformat a LaTeX table, to space-align columns.
#   This has no effect on the pdf, but improves readability of the source.
#   This tool takes **only the innards** of a single table
#   (the rows, containing columns separated by &)
#   and tries to reformat it.
#   May eat your cat.

# Usage example:
#   Most effective when called using a keybind in your favorite editor.
#   spacealign_latex_table.py < original > reformatted


import sys

def column_widths(lines):
    for line in lines:
        columns = line.split('&')
        if len(columns) < 2:
            continue
        stripped = [col.strip() for col in columns]
        widths = [len(col) for col in stripped]
        yield widths

def max_widths(all_widths):
    # transpose from by-rows to by-cols
    by_col = list(zip(*all_widths))
    widths = [max(col) for col in by_col]
    return widths

def make_formats(widths):
    formats = [' {:' + str(w) + '} ' if w > 0 else ''
               for w in widths]
    return formats

def reformat(lines, formats):
    for line in lines:
        columns = line.split('&')
        stripped = [col.strip() for col in columns]
        if len(columns) != len(formats):
            yield line
            continue
        reformatted = [fmt.format(col)
                       for (fmt, col)
                       in zip(formats, stripped)]
        joined = '&'.join(reformatted)
        # extra space at ends
        joined = joined[1:-1]
        yield joined

def main():
    lines = sys.stdin
    lines = [line.rstrip('\n') for line in lines]
    all_widths = column_widths(lines)
    widths = max_widths(all_widths)
    formats = make_formats(widths)
    for line in reformat(lines, formats):
        print(line)


if __name__ == '__main__':
    main()
