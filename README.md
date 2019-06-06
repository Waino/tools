# Command line tools

A collection of small tools that you may find useful

## Tools

### findt.py

Given a unique pattern matching the command line of a running command (COMMAND column in *ps* output),
tries to find the terminal in which that command is running, and focus the terminal window.

Useful if you have way too many terminals open.

> `findt.py a_file_open_in_some_editor`

### followlatex.py

Turns any editor into a live-preview LaTeX editor.

Uses inotify to follow writes to the LaTeX source file.
Whenever the file changes, latexrun is used to recompile the pdf.
Use together with a pdf editor that notices when the pdf changes,
e.g. evince.

> `followlatex.py my_latex_source.tex`

If you are using \input to include another file,
you can track changes to that file as well by giving it as a
second argument.


> `followlatex.py main.tex included_tikz_figure.tex`

### inject\_script\_step.py

If you have a project consisting of several scripts that are intended to be
run in order, a good self-documenting convention is to prefix them with
numbers `01_foo.sh` `02_bar.sh` etc. This tool helps the renaming when you
notice that you need to add a step in the middle.

Add a new step number 05, by renaming the current 05 to 06 and incrementing
all the following ones by one.

>     `inject_script_step.py 5`


### morphcount.py

Just a simple way to make a word or morph occurrence count list.
More efficient and user-friendly than using shell builtins.

> `morphcount.py < corpus > word_counts`

### reflow\_latex.py

In LaTeX source, it is a good idea to put each sentence on a new line.
This allows line-oriented diff tools to give much more useful output.
This convention is particularly useful when combining LaTeX with git.

This tool takes text that doesn't fit the convention and tries to reformat it.
May eat your cat.

Most effective when called using a keybind in your favorite editor.

### regexrename.py

Allows using regular expressions to mass-rename files.
Has a dryrun mode `-n` to help you avoid mistakes.
Checks for name collisions before starting the renaming.
If a collision is detected, nothing is done, to avoid leaving the
files in an inconsistent state.

More user-friendly than using shell builtins.

> `regexrename [-h] [-s] [-n] [--cleanup] [from] [to]`

Add "prefix\_" to all filenames (e.g. foo -> prefix\_foo)
>     `regexrename ^ prefix_`

See how your filenames would look with vowels replaced by A
>     `regexrename.py -n "[aeiou]" A`

Swap the first two characters in all filenames
>     `regexrename.py "^(.)(.)" "\2\1"`

Clean up some common unwanted characters from all filenames
>     `regexrename.py --cleanup`

### spacealign\_latex\_table.py

Tries to reformat a LaTeX table, to space-align columns.
This has no effect on the pdf, but improves readability of the source.
This tool takes **only the innards** of a single table
(the rows, containing columns separated by &)
and tries to reformat it.
May eat your cat.

Most effective when called using a keybind in your favorite editor.

### xtitle.sh

Just a quick hack to set the title of xterm-compatible terminals.
For those who don't remember their shell escapes by heart anymore.

## Dependencies

**findt.py** depends on the *xdotool* linux package.

**followlatex.py** depends on the *envoy* and *inotify* python packages, and *latexrun*.
[https://github.com/aclements/latexrun](https://github.com/aclements/latexrun)

**reflow\_latex.py** depends on *numpy*.
