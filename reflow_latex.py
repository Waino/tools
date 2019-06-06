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
#   In LaTeX source, it is a good idea to put each sentence on a new line.
#   This allows line-oriented diff tools to give much more useful output.
#   This convention is particularly useful when combining LaTeX with git.
#   This has no effect on the pdf, but improves readability of the source.
#
#   This tool takes text that doesn't fit the convention and tries to reformat it.
#   May eat your cat.

# Usage example:
#   Most effective when called using a keybind in your favorite editor.
#   reflow_latex.py < original > reformatted

import argparse
import codecs
import numpy as np
import re
import sys

#CHARS_MIN = 40
CHARS_OPT = 80
CHARS_LONG = 115
CHARS_MAX = 120

COST_CHAR = 0.8
COST_LINE = 1. * (CHARS_MAX - CHARS_OPT)
COST_LONG = 5.
COST_TOOLONG = 100.

COST_SHORTDELIMITED = 80.
COST_BAD = 8.

COST_FULLSTOP = -55.
COST_COMMA = -38.
COST_FUNC = -15.

FULLSTOPS = '.!?'
COMMAS = ',:'
FUNC_WORDS = ['a', 'and', 'are', 'as', 'but', 'by', 'for', 'having',
              'in', 'is', 'of', 'or', 'that', 'this', 'the', 'to', 'using',
              'were', 'where', 'when', 'which', 'with', 'without']
DELIMS = ['{}', '()', '[]', ('``', "''")]

RE_COMMENT = re.compile(r'(?<!\\)%')
RE_SINGLECOMMAND = re.compile(r'^\\.*}%?$')
RE_ENDBREAK = re.compile(r'\\\\$')
RE_STARTSPACE = re.compile(r'^[ \t]')   # don't match newlines

SHORT_DELIM = 4     # tokens

# FIXME: unhandled patterns:
# X, Y and Z
# FIXME: de-fancify dashes and quotes

class Span(object):
    def __init__(self, parts,
                 segment=True, join_left='allow', join_right='allow'):
        if isinstance(parts, str):
            self.content = parts
        else:
            self.content = ''.join(parts).strip()
        self.segment = segment
        self.join_left = join_left
        self.join_right = join_right

    def tokenize(self):
        # here we only want to split at space, never strand punctuation etc.
        if self.segment:
            self.content = self.content.split()
        else:
            self.content = [self.content]
        return self


def paragraphs(lines, hyphenated=True):
    current = []
    for line in lines:
        if len(RE_STARTSPACE.findall(line)) > 0:
            # don't reflow indented lines?
            yield Span(current)
            yield Span(line.strip('\n'), segment=False,
                       join_left='forbid', join_right='forbid')
            current = []
            continue
        line = line.strip()
        if len(line) == 0:
            yield Span(current)
            # blank lines indicate paragraph breaks
            yield Span('', segment=False, join_right='forbid')
            current = []
            continue
        if len(RE_COMMENT.findall(line)) > 0:
            yield Span(current)
            # don't reflow lines with comments
            # but allow appending comment to previous line
            yield Span(line, segment=False,
                       join_left='prefer', join_right='forbid')
            current = []
            continue
        if RE_SINGLECOMMAND.match(line):
            yield Span(current)
            # don't reflow single-command lines
            yield Span(line, segment=False,
                       join_left='forbid', join_right='forbid')
            current = []
            continue
        sep = ' '
        if hyphenated and line[-1] == '-':
            sep = ''
            line = line[:-1]
        current.append(line)
        current.append(sep)
        if len(RE_ENDBREAK.findall(line)) > 0:
            # don't remove break after \\
            yield Span(current, join_right='forbid')
            current = []
    yield Span(current)


def static_costs(line):
    """Static cost of breaking after the token at index."""
    costs = np.zeros(len(line))
    open_delims = [None] * len(DELIMS)
    for (i, token) in enumerate(line):
        if len(token) == 0:
            continue
        if token[-1] in FULLSTOPS:
            costs[i] += COST_FULLSTOP
        if token[-1] in COMMAS:
            costs[i] += COST_COMMA
        if token.lower() in FUNC_WORDS:
            costs[i] -= COST_FUNC          # penalty after
            if i > 0:
                costs[i - 1] += COST_FUNC  # bonus before
        for (j, delim) in enumerate(DELIMS):
            if delim[0] in token and not delim[1] in token:
                # opened but not immediately closed
                open_delims[j] = i
            if delim[1] in token and open_delims[j] is not None:
                if open_delims[j] >= i - SHORT_DELIM:
                    costs[open_delims[j]:i] += COST_SHORTDELIMITED
                open_delims[j] = None
    return costs


def line_cost(line):
    n_chars = len(' '.join(line))
    extra = COST_TOOLONG if n_chars > CHARS_MAX else 0
    if n_chars > CHARS_LONG:
        extra += COST_LONG
    return np.abs(n_chars - CHARS_OPT) + COST_LINE + extra


def noblank(tokens):
    return [x for x in tokens if len(x) > 0]


def segment(line):
    line = [''] + line
    n_tokens = len(line)
    scosts = static_costs(line)
    dpcost = np.array([np.infty] * n_tokens)
    dpcost[0] = 0
    dpback = np.zeros(n_tokens, dtype=int)
    dpback[0] = -1
    current = np.zeros(n_tokens)
    for j in range(1, n_tokens):
        current[:] = np.infty
        for i in range(j):
            start_to_i = dpcost[i]
            i_to_j = line_cost(line[(i + 1):j])
            current[i] = start_to_i + i_to_j
        best = np.argmin(current)
        dpback[j] = best
        dpcost[j] = current[best] + scosts[j - 1]
    out = []
    prevcursor = n_tokens
    cursor = dpback[-1]
    while cursor > -1:
        out.append(' '.join(noblank(line[cursor:prevcursor])))
        prevcursor = cursor
        cursor = dpback[cursor]
    return reversed(out)


def join_spans(spans):
    previous = None
    for span in spans:
        if previous is None:
            previous = span
            continue
        if previous.join_right == 'forbid':
            yield previous
            previous = span
            continue
        if span.join_left == 'prefer':
            previous.content.extend(span.content)
            continue
        yield previous
        previous = span
    if previous is not None:
        yield previous


def segment_spans(spans):
    for span in spans:
        if span.segment:
            segments = segment(span.content)
        else:
            segments = span.content
        for seg in segments:
            yield seg + '\n'


def reflow(items):
    items = paragraphs(items)
    items = (item.tokenize() for item in items)
    items = join_spans(items)
    items = segment_spans(items)
    for item in items:
        yield item


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', default='-', nargs='?')
    parser.add_argument('outfile', default='-', nargs='?')
    return parser


def main(argv):
    parser = get_parser()
    args = parser.parse_args(argv)
    if args.infile == '-':
        #infile = codecs.getreader('utf-8')(sys.stdin)  # PY2
        infile = sys.stdin
    else:
        infile = codecs.open(args.infile, 'r', encoding='utf-8')
    if args.outfile == '-':
        #outfile = codecs.getwriter('utf-8')(sys.stdout)
        outfile = sys.stdout
    else:
        outfile = codecs.open(args.outfile, 'w', encoding='utf-8')
    for item in reflow(infile.readlines()):
        outfile.write(item)


if __name__ == '__main__':
    main(sys.argv[1:])
