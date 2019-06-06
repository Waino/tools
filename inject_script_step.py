#!/usr/bin/env python3
# coding=utf-8

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
#   If you have a project consisting of several scripts that are intended to be
#   run in order, a good self-documenting convention is to prefix them with
#   numbers 01_foo.sh 02_bar.sh etc. This tool helps the renaming when you
#   notice that you need to add a step in the middle.
# 
# Usage example:
#   Add a new step number 05, by renaming the current 05 to 06 and incrementing
#   all the following ones by one.
#       inject_script_step.py 05

import argparse
import collections
import os
import re
import sys

RE_NUMBER = re.compile(r'^([0-9]+)_(.*)')

Action = collections.namedtuple('Action', ['frm', 'to'])

parser = argparse.ArgumentParser(
    prog='inject_script_step',
    formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('-n', '--dryrun', dest='dryrun',
                    default=False, action='store_true',
                    help='Only print what would be done.')

parser.add_argument('index', metavar='index', type=int)


class Renamer(object):
    def __init__(self, transform):
        self.schedule = []
        self.transform = transform
        self.failed = 0

    #def decode(self, fnames):
    #    result = []
    #    for fname in fnames:
    #        try:
    #            fname = unicode(fname.decode('utf-8'))
    #            result.append(fname)
    #        except UnicodeDecodeError as e:
    #            print(fname)
    #            raise e
    #    return result

    def visit(self, dirname, fnames):
        #fnames = self.decode(fnames)

        fnames.sort()
        local = []
        for frm in fnames:
            to = self.transform(frm)
            self.check(frm, to, local, dirname)
            # Unchanged files are added to local (can still conflict)
            local.append(Action(frm, to))
            if frm == to:
                # Unchanged files need not be scheduled for renaming though
                continue
            self.schedule.append(Action(
                os.path.join(dirname, frm),
                os.path.join(dirname, to)))

    def check(self, frm, to, local, dirname):
        for item in local:
            if to == item.to:
                print(
                    'Conflict: "{}" and "{}" -> "{}"'.format(
                        os.path.join(dirname, frm),
                        os.path.join(dirname, item.frm),
                        os.path.join(dirname, to)),
                    file=sys.stderr)
                self.failed += 1
                if self.failed >= MAX_ERRORS:
                    raise Exception('FATAL: too many errors')

    def execute(self, func):
        assert self.failed == 0
        # reversed, so nested files are renamed before containing dir
        for action in reversed(self.schedule):
            func(action.frm, action.to)

def inject_transform(index):
    def inner(frm):
        m = RE_NUMBER.match(frm)
        if not m:
            # non-numbered files are unchanged
            return frm
        old = int(m.group(1))
        tail = m.group(2)
        if old < index:
            # lower indices are unchanged
            return frm
        new = old + 1
        to = '{:02}_{}'.format(new, tail)
        return to
    return inner

def dryrun(frm, to):
    print('mv -i "{}" "{}"'.format(frm, to))


def rename(frm, to):
    assert not os.path.exists(to)
    os.rename(frm, to)


def main(args):
    trafo = inject_transform(args.index)
    r = Renamer(trafo)

    r.visit('.', os.listdir('.'))

    if r.failed > 0:
        raise Exception('Conflicts detected, will not rename')
    if args.dryrun:
        func = dryrun
    else:
        func = rename
    r.execute(func)

if __name__ == '__main__':
    main(parser.parse_args(sys.argv[1:]))
