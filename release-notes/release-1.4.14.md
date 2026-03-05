### Release 1.4.14

This release focuses on making **tmux-fzf-links** faster, more reliable, and easier to debug!

#### Performance Improvements
- **Bulk Option Fetch**: Optimized startup by fetching all tmux options in a single call, reducing load time from ~80ms to ~8ms.
- **Zero-Fork Expansion**: Replaced subshell-based `eval` expansion in the bootstrap script with pure Bash string manipulation, reducing expansion time to 0ms.
- **Pre-Quoted Python**: Improved efficiency by pre-quoting the Python path during bootstrap to avoid unnecessary subshells on keypress.

#### Fixes & Enhancements
- **Tilde Expansion**: Added surgical `~/` expansion for complex command strings (like custom editors) in Python, ensuring robust path handling for all user configurations.
- **Improved Logging**: Added `INFO` level tracing for spawned processes, making it easier to troubleshoot command execution.
- **Error Handling**: Fixed several internal exceptions and missing imports (`CommandFailed`, `NotSupportedPlatform`).
- **File Permissions**: Fixed `__main__.py` file permissions and updated `.gitignore`.

#### Documentation
- **Troubleshooting**: Added a new Troubleshooting section to the `README.md` covering common issues, logging, and performance.
- **Performance Benchmarks**: Documented plugin bootstrap time (~15ms total) and explained path/variable expansion behavior.
- **Installation**: Updated instructions for installing specific release versions using `zinit`.

#### Build & CI
- **Draft Releases**: Configured automated publishing to create draft releases for better version control.
