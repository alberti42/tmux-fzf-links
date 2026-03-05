# Change log

## New features

- Added actions through new key bindings `ctrl`-`r` and `ctrl`-`d` for revealing files in the system's file manager and for opening files with the system's default opener.
- Prevent binary files from being opened in the editor
- When a directory is selected, it `cd` into the selected directory

## Breaking changes

- The result of `post_handler` is of type `PostHandledMatch`, which is a dictionary with fields depending on the configured `opener`. The list provided before should be converted to a dictionary, with the first argument passed to the dictionary key `cmd` and the resting arguments passed as a list to the dictionary key `args`. Optionally, one can provide a dictionary key `file` which is used to reveal and open the field with default file associations.

- To copy the selection to the clipboard, the new key binding with `ctrl`-`c` replaces the old key binding with META-ENTER. New key bindings for the two new actions `ctrl`-`d` and `ctrl`-`r` for the system's default file association and system's file manager have been introduced.

## Improvements

- Several improvements under the ho, especially about type hinting, making the code more robust.

