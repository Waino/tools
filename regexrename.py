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
#   Allows using regular expressions to mass-rename files.
#   Has a dryrun mode -n to help you avoid mistakes.
#   Checks for name collisions before starting the renaming.
#   If a collision is detected, nothing is done, to avoid leaving the
#   files in an inconsistent state.
#
#   More user-friendly than using shell builtins.
# 
# Usage example:
#   regexrename [-h] [-s] [-n] [--cleanup] [from] [to]
#
#   Add "prefix_" to all files (e.g. foo -> prefix_foo)
#       regexrename ^ prefix_
#   See how your files would look with vowels replaced by A
#       regexrename.py -n "[aeiou]" A
#   Clean up some common unwanted characters from all files
#       regexrename.py --cleanup

import argparse
import collections
import os
import re
import sys

RE_UNWANTED = re.compile(r'[^A-Za-z0-9.+_-]')
CLEANUP_MAP = {
    'Å': 'AA',
    'Ä': 'A',
    'Ö': 'O',
    'Ü': 'U',
    'å': 'aa',
    'ä': 'a',
    'ö': 'o',
    'ü': 'u',
    '&': 'and'}

MAX_ERRORS = 30

Action = collections.namedtuple('Action', ['frm', 'to'])

parser = argparse.ArgumentParser(
    prog='regexrename',
    formatter_class=argparse.RawDescriptionHelpFormatter)
# ex: regexrename.py "^(.)(.)" "\2\1"

parser.add_argument('-s', '--shallow', dest='shallow',
                    default=False, action='store_true',
                    help='Do not recursively descend into subdirs.')
parser.add_argument('-n', '--dryrun', dest='dryrun',
                    default=False, action='store_true',
                    help='Only print what would be done.')
parser.add_argument('--cleanup', dest='cleanup',
                    default=False, action='store_true',
                    help='Common cleanup transformations.')

parser.add_argument('frm', metavar='from', type=str, nargs='?')
parser.add_argument('to', metavar='to', type=str, nargs='?')


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


def regex_transform(pattern, to):
    regex = re.compile(pattern)

    def inner(frm):
        return regex.sub(to, frm)
    return inner


def cleanup_transform(frm):
    to = frm
    for (a, b) in CLEANUP_MAP.items():
        to = to.replace(a, b)
    to = RE_UNWANTED.sub('_', to)
    return to


def dryrun(frm, to):
    print('mv -i "{}" "{}"'.format(frm, to))


def rename(frm, to):
    assert not os.path.exists(to)
    os.rename(frm, to)


def main(args):
    if args.cleanup and (args.frm is not None or args.to is not None):
        raise Exception('cleanup can not be used with from and to')
    if args.frm is not None and args.to is None:
        raise Exception('if from is specified, to must also be')
    if not args.cleanup and args.frm is None:
        raise Exception('too few arguments')

    if args.cleanup:
        trafo = cleanup_transform
    else:
        trafo = regex_transform(args.frm, args.to)
    r = Renamer(trafo)

    if args.shallow:
        r.visit('.', os.listdir('.'))
    else:
        for dirpath, _, filenames in os.walk(str('.')):
            r.visit(dirpath, filenames)

    if r.failed > 0:
        raise Exception('Conflicts detected, will not rename')
    if args.dryrun:
        func = dryrun
    else:
        func = rename
    r.execute(func)

if __name__ == '__main__':
    main(parser.parse_args(sys.argv[1:]))
