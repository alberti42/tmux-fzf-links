# 🚀 tmux-fzf-links

**tmux-fzf-links** is a versatile tmux plugin that allows you to search for and open links directly from your terminal using fuzzy search powered by [fzf](https://github.com/junegunn/fzf). The plugin supports both default and user-defined schemes, offering unmatched flexibility and integration with tmux popup windows.

The default schemes include recognition of:

- local files wih relative and absolute paths (192.168.1.42:8000)
- Python code error, recognizing the line where the error was generated
- web addresses (e.g. https://...)
- IP addresses (192.168.1.42:8000)
- git addresses (e.g., `git@github.com:alberti42/dotfiles.git`)

The plugin was originally inspired by [tmux-fzf-url](https://github.com/wfxr/tmux-fzf-url).

---

## 🌟 Features

- **Fuzzy Search Links**: Quickly locate and open links appearing in your terminal output.
- **Default and Custom Schemes**: Use pre-configured schemes or define your own with custom handlers for pre- and post-processing.
- **Integration with tmux Popup Windows**: Provides a seamless user experience within tmux sessions.
- **Flexible Open Commands**: Configure your favorite editor, browser, or custom command to open links.
- **Dynamic Logging**: Output logs to tmux messages and/or a file, with adjustable verbosity.

---

## 📦 Installation

### Prerequisites

- **tmux** (tested with 3.4)
- **fzf**
- **Python** (tested with Python 3.11)

### Install via zinit

Add the following to your `.zshrc`:

```zsh
zinit load tmux-plugins/tmux-fzf-links
```

Alternatively, clone this repository and source the `fzf-links.tmux` file in your `.tmux.conf`:

```sh
git clone https://github.com/alberti42/tmux-fzf-links.git ~/.tmux/plugins/tmux-fzf-links
```

---

## ⚙️ Configuration

Default options are already provided. However, you can customize all options by adding the following lines to your `.tmux.conf`:

```tmux
# === tmux-fzf-links ===
set-option -g @fzf-links-key o
set-option -g @fzf-links-history-limit 'screen'
set-option -g @fzf-links-editor-open-cmd '/path/to/editor'
set-option -g @fzf-links-browser-open-cmd '/path/to/browser'
set-option -g @fzf-links-fzf-display-options '-w 100% -max-h 20 --multi -0 --no-preview'
set-option -g @fzf-links-path-extension '/path/to/plugin/bin'
set-option -g @fzf-links-loglevel-tmux 'WARNING'
set-option -g @fzf-links-loglevel-file 'INFO'
set-option -g @fzf-links-log-filename '~/log.txt'
set-option -g @fzf-links-python-path 'python3'
set-option -g @fzf-links-user-schemes-path '~/.local/share/tmux-fzf-links/user_schemes.py'

run-shell "~/.local/share/tmux-fzf-links/fzf-links.tmux"
```

Replace the placeholders with appropriate paths and commands for your environment.

---

## 🖱️ Usage

1. Start tmux.
2. Press the configured key (default: `o` as for `open`) to activate **tmux-fzf-links**.
3. Select a link using the fuzzy search interface.
4. The link will be opened using the configured command (editor, browser, or custom).

---

## 🛠️ Defining Schemes

### Default Schemes

The plugin comes with built-in schemes for common patterns, including URLs, file paths, and Git repositories. These are defined in `default_schemes.py`.

Example:

```python
default_schemes = {
    "<url>": {
        "opener": OpenerType.BROWSER,
        "regex": re.compile(r"https?://[^\s]+"),
        "pre_handler": None,
        "post_handler": None,
    },
    "<file>": {
        "opener": OpenerType.CUSTOM,
        "regex": re.compile(r"\~?[a-zA-Z0-9_\/\-]+\.[a-zA-Z0-9]+"),
        "pre_handler": file_pre_handler,
        "post_handler": file_post_handler,
    },
}
```

### Adding Custom Schemes

To extend functionality, define your own schemes in a separate file (e.g., `user_schemes.py`):

```python
user_schemes = {
    "<ip>": {
        "opener": OpenerType.BROWSER,
        "regex": re.compile(r"[0-9]{1,3}(\.[0-9]{1,3}){3}"),
        "pre_handler": ip_pre_handler,
        "post_handler": ip_post_handler,
    },
}
```

Specify the path to your scheme file in the configuration.

---

## 🔍 Logging

Control logging levels via these options:

- `@fzf-links-loglevel-tmux`: Adjust tmux log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- `@fzf-links-loglevel-file`: Set log verbosity for file logs.
- `@fzf-links-log-filename`: Specify the log file location.

---

## 🧩 Extensibility

The plugin's Python-based architecture enables advanced users to:

1. Define intricate regular expressions.
2. Implement pre- and post-processing functions for custom behaviors.
3. Extend functionality without modifying the core code.

---

## 🤝 Contributing

Contributions are welcome! Please fork this repository and submit a pull request for enhancements or bug fixes, or simply report any issues in the [GitHub repository](https://github.com/alberti42/tmux-fzf-links/issues)

## ❤️ Donations

I would be grateful for any donation to support the development of this plugin.

[<img src="images/buy_me_coffee.png" width=300 alt="Buy Me a Coffee QR Code"/>](https://buymeacoffee.com/alberti)

## 👨‍💻 Author

- **Author:** Andrea Alberti
- **GitHub Profile:** [alberti42](https://github.com/alberti42)
- **Donations:** [![Buy Me a Coffee](https://img.shields.io/badge/Donate-Buy%20Me%20a%20Coffee-orange)](https://buymeacoffee.com/alberti)


---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
