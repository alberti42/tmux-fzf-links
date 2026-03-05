# Change log

## Bug fixes

- Added checks for maximum supported file name length by the file system, which also supports UTF8-encoded filenames. Added handling exception errno.ENAMETOOLONG as a last resort, though this handling mechanism should never be triggered when the length check works properly. This fixes the issue https://github.com/alberti42/tmux-fzf-links/issues/10.
