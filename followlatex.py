#!/usr/bin/env python

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
#   Turns any editor into a live-preview LaTeX editor.
#
#   Uses inotify to follow writes to the LaTeX source file.
#   Whenever the file changes, latexrun is used to recompile the pdf.
#   Use together with a pdf editor that notices when the pdf changes,
#   e.g. evince.
#
#   If you are using \input to include another file,
#   you can track changes to that file as well by giving it as a
#   second argument.
# 
# Usage example:
#   followlatex.py my_latex_source.tex
#   followlatex.py main.tex included_tikz_figure.tex
#
# Dependencies:
#   envoy, inotify, latexrun, evince

import argparse
import envoy
import inotify.adapters
import os
import sys


def tex(filename):
    base, ext = os.path.splitext(filename)
    return '{}.tex'.format(base)

def pdf(filename):
    base, ext = os.path.splitext(filename)
    return '{}.pdf'.format(base)

def swp(filename):
    return '.{}.swp'.format(filename)


class InotifyWrapper(object):
    def __init__(self):
        self.ina = inotify.adapters.Inotify()
        # {path}
        self.directories = set()
        # {(dir, filename, mask) -> callback}
        self.callbacks = {}
        self.must_exit = False

    def directory(self, directory):
        if directory not in self.directories:
            self.ina.add_watch(directory)

    def add_watch(self,
                  directory,
                  filename,
                  callback,
                  mask=inotify.constants.IN_CLOSE_WRITE):
        directory = directory.encode()
        filename = filename.encode()
        self.directory(directory)
        self.callbacks[(directory, filename, mask)] = callback

    def rm_watch(self, directory):
        self.ina.remove_watch(directory)
        if directory in self.directories:
            self.directories.remove(directory)

    def event_loop(self):
        try:
            for event in self.ina.event_gen():
                if event is not None:
                    (header, type_names, watch_path, filename) = event
                    key = (watch_path, filename, header.mask)
                    if key in self.callbacks:
                        self.callbacks[key](event)
        finally:
            self.close()

    def close(self):
        print('Cleaning up')
        for directory in self.directories:
            self.rm_watch(directory)
        

class LatexFollower(object):
    def __init__(self, iw, mainfilename, editfilename=None):
        self.iw = iw
        mainfilename = tex(mainfilename)
        self.sourcefilename = mainfilename
        self.renderfilename = pdf(mainfilename)
        self.evince = None
        self.launch()

        iw.add_watch('.', mainfilename, self.render)
        if editfilename is not None:
            editdir, editfilename = os.path.split(editfilename)
            if len(editdir) == 0:
                editdir = '.'
            iw.add_watch(editdir, editfilename, self.render)
        # not hooking swp(editfilename) to exit: too unreliable

    def launch(self):
        #if not os.path.exists(self.renderfilename):
        self.render()
        self.evince = envoy.connect('evince {}'.format(self.renderfilename))

    def render(self, event=None):
        #envoy.run('xelatex -halt-on-error {}'.format(self.sourcefilename))
        r = envoy.run('latexrun --latex-cmd xelatex {}'.format(self.sourcefilename))
        # latexrun cleans up output, so we can show it here
        print(r.std_out)

    def exit(self, event=None):
        print('Must exit')
        self.iw.must_exit = True


def get_parser():
    parser = argparse.ArgumentParser('followlatex.py')
    parser.add_argument('mainfile', help='Main tex file')
    parser.add_argument('editfile', nargs='?',
        help='File being edited (if not the same as mainfile)')
    return parser

def main(args):
    iw = InotifyWrapper()
    follower = LatexFollower(iw, args.mainfile, args.editfile)
    iw.event_loop()


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args(sys.argv[1:])
    main(args)
