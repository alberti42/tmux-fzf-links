# Change log

## Bug fixes

- Fixed regex with incompatibility with Python 3.10. Related issue: https://github.com/alberti42/tmux-fzf-links/issues/6
- Fixed bug when opening files containing spaces
- Fixed small bug as reported in https://github.com/alberti42/tmux-fzf-links/issues/12 affecting older Python versions

## Improvements under the hood

- Improved handling of critical errors crashing Python script. If the Python script unexpectedly crashes before it can log errors, then the command and Python error are shown on the screen so that one can possibly debug it.
