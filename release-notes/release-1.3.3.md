# Change log

## Improvements:

- capture the screen as it is actually displayed. This means that capturing links also works in tmux copy mode: it will correctly capture the displayed links when scrolling back through the buffer.
- removed escaped characters directly when capturing tmux screen. No longer required to remove escaped characters afterward by the Python script.
- extended range of bytes checked to determine whether it is a binary or non-binary file, making the detection of binary files more robust

