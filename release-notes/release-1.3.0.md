# Change log

## New features

- Match file with line number identified by `:` such `/this/file.txt:123` to open the file at line number 123.
- Added option to copy the selection to the clipboard and tmux buffer by pressing `META`+`ENTER`
- Correctly handle (i.e., match) file names with diacritics (important for languages like German and French)
- Implemented backtracking when evaluating regular expression results in an invalid match; this allows testing multiple alternative regular expressions (see e.g. `file_scheme:SchemeEntry` in `default_schemes.py`).

## Minor changes

- Changed fzf options: removed `-0` and added `--track`
- Refactored code for logging (under-the-hood changes)
