# 🚀 tmux-fzf-links

**tmux-fzf-links** is a versatile tmux plugin that allows you to search for and open links directly from your terminal using fuzzy search powered by [fzf](https://github.com/junegunn/fzf). The plugin supports both default and user-defined schemes, offering unmatched flexibility and integration with tmux popup windows.

The default schemes include recognition of:

- local files with relative and absolute paths (192.168.1.42:8000)
- Python code error where it recognizes the line at which the error was generated
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
- **Colorized Links**: Enhance readability with colorized links, using `$LS_COLORS` for files and directories.

---

## 🧩 Extensibility

The plugin's Python-based architecture enables advanced users to:

1. Define intricate regular expressions.
2. Implement pre- and post-processing functions for custom behaviors.
3. Extend functionality without modifying the core code.

---

## 🎥 Screencast

Watch the plugin in action to see how it enhances your tmux workflow!

<img src="https://github.com/alberti42/tmux-fzf-links/blob/master/images/screencast.gif" alt="Screencast" />

---

## 📦 Installation

### Using TPM (Tmux Plugin Manager)

To install the plugin with [TPM](https://github.com/tmux-plugins/tpm), add the following lines to your `.tmux.conf`:

```tmux
# List of plugins
set -g @plugin 'alberti42/tmux-fzf-links'
set -g @plugin 'tmux-plugins/tpm'

run '~/.tmux/plugins/tpm/tpm'
```

After adding the configuration, reload your tmux environment by pressing:

```plaintext
prefix + r
```

Then install the plugin by pressing:

```plaintext
prefix + I
```

After installation, the `.tmux` file will be located at:

```plaintext
$HOME/.tmux/plugins/tmux-fzf-links/fzf-links.tmux
```

### Using zinit

To install the plugin with [zinit](https://github.com/zdharma-continuum/zinit), add the following to your `.zshrc`:

```zsh
zinit ice as'null' nocompile'!' depth=1 lucid wait
zinit light @alberti42/tmux-fzf-links
```

This configuration ensures the plugin is loaded with the turbo (delayed) option (`wait`) for optimized shell startup. After installation, the `.tmux` file `fzf-links.tmux` will be located at:

```plaintext
$ZINIT_HOME/plugins/alberti42---tmux-fzf-links/fzf-links.tmux
```

### Manual Installation

To manually install the plugin, clone the repository into a standard directory such as `$HOME/.tmux/plugins/`. Use the following command:

```sh
git clone --depth=1 https://github.com/alberti42/tmux-fzf-links.git ~/.tmux/plugins/tmux-fzf-links
```

Using `--depth=1` ensures only the latest commit is downloaded, minimizing unnecessary download of the commit history. After installation, the `.tmux` file will be located at:

```plaintext
$HOME/.tmux/plugins/tmux-fzf-links/fzf-links.tmux
```

### Starting the Plugin

If you did not use TPM, but did a manual installation or used zinit, ensure the plugin is loaded in your `.tmux.conf`. After installing it, add the following line to your `.tmux.conf`:

```tmux
run-shell "~/.tmux/plugins/tmux-fzf-links/fzf-links.tmux"
```

or, if you used zinit,

```tmux
run-shell "$ZINIT_HOME/plugins/alberti42---tmux-fzf-links/fzf-links.tmux"
```

replacing `$ZINIT_HOME` with the actual value of your zinit home directory.


## ⚙️ Configuration

Default options are already provided. However, you can customize all options by adding the following lines to your `.tmux.conf`:

```tmux
# === tmux-fzf-links ===
# set-option -g @fzf-links-key o
# set-option -g @fzf-links-history-lines "0"
set-option -g @fzf-links-editor-open-cmd "tmux new-window -n 'emacs' /usr/local/bin/emacs +%line '%file'"
set-option -g @fzf-links-browser-open-cmd "/path/to/browser '%url'"
set-option -g @fzf-links-fzf-display-options "-w 100% --maxnum-displayed 20 --multi -0 --no-preview"
# set-option -g @fzf-links-path-extension "/usr/local/bin"
# set-option -g @fzf-links-loglevel-tmux "WARNING"
# set-option -g @fzf-links-loglevel-file "DEBUG"
# set-option -g @fzf-links-log-filename "~/log.txt"
set-option -g @fzf-links-python "python3"
# set-option -g @fzf-links-python-path "~/.virtualenvs/my_special_venv/lib/python3.11/site-packages"
# set-option -g @fzf-links-user-schemes-path "~/.tmux/plugins/tmux-fzf-links/user_schemes/user_schemes.py"
set-option -g @fzf-links-use-colors on
# set-option -g @fzf-links-ls-colors-filename "~/.cache/zinit/ls_colors.zsh"

run-shell "~/.local/share/tmux-fzf-links/fzf-links.tmux"
```

### Notes

1. **`@fzf-links-editor-open-cmd`**: This option specifies the command for opening the editor. In the command, the placeholders `%file` and `%line` are automatically replaced with the fully-resolved file path and the line number, respectively. Note that in general editors have  different syntax to specify how to open a file at a given line.

   To open a terminal-based editor, such as Emacs or Vim, use `tmux new-window` to ensure the editor opens in a new tmux window. Example:  
   ```tmux
   set-option -g @fzf-links-editor-open-cmd 'tmux new-window -n "emacs" /usr/local/bin/emacs'
   ```

   For desktop applications, such as Sublime Text, you can directly provide the path to the editor. Example:  
   ```tmux
   set-option -g @fzf-links-editor-open-cmd '/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl'
   ```

2. **`fzf-links-browser-open-cmd`**: This option specifies the command for opening the browser. User `%url` as the placeholder for the url to be opened.

3. **`@fzf-links-fzf-display-options`**: This option specifies the arguments passed to `fzf-tmux` and, subsequently, to `fzf`. Refer to the respective man pages of [`fzf-tmux`](https://github.com/junegunn/fzf#fzf-tmux) and [`fzf`](https://github.com/junegunn/fzf#options) for detailed documentation of the available arguments.

   - **`--maxnum-displayed`**: A custom option added by this plugin to limit the maximum number of items displayed in the `fzf` popup. If the total matches exceed this number, the plugin ensures that only up to `--maxnum-displayed` items are shown. This is particularly helpful for avoiding oversized popups when many matches are present.

   - **Automatic Height Calculation**: If `-h` (height) is not specified in the options, the plugin dynamically computes the necessary popup height to fit all items, up to the value set in `--maxnum-displayed`. If fewer matches exist, the height adjusts accordingly.

   Example:  
   ```tmux
   set-option -g @fzf-links-fzf-display-options '-w 100% --maxnum-displayed 10 --multi -0 --no-preview'
   ```

4. **`history-lines`**: An integer number determining how many extra lines of history to consider. By default, it is set to 0.

5. **`@fzf-links-ls-colors-filename`**: This option is not strictly necessary if `$LS_COLORS` is available in the environment. Use it only if `tmux` is launched directly as the first process in the terminal, bypassing the shell initialization where `$LS_COLORS` is set.

6. **`@fzf-links-path-extension`**: This option is also not strictly necessary. It is only required if `fzf-tmux` or `tmux` binaries are not in the `$PATH` that was available when `tmux` started. The plugin only requires these two processes.

Replace the placeholders with appropriate paths and commands for your environment.

7. **`fzf-links-python`** and **`fzf-links-python-path`**: These two options allow specifying the path to the Python interpreter and, if needed, to a Python `site-packages` directory, which is appended to `$PYTHONPATH`. The plugin does not rely on any external dependencies. However, you may want to import external modules installed in `site-packages` to extend the functionality of the plugin in `user_schemes`.

8. 🔍 **Logging**: Control logging levels via these options:

   - `@fzf-links-loglevel-tmux`: Adjust tmux log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
   - `@fzf-links-loglevel-file`: Set log verbosity for file logs.
   - `@fzf-links-log-filename`: Specify the log file location. Omit this property or set it to an empty string to prevent logging to file.

---

## 🖱️ Usage

1. Start tmux.
2. Press the configured key (default: `o` as for `open`) to activate **tmux-fzf-links**.
3. Select a link using the fuzzy search interface.
4. The link will be opened using the configured command (editor, browser, or custom).

---

## 🛠️ Defining Schemes

### Default Schemes

The plugin uses a **list of dictionaries** to define schemes, where each dictionary represents a single scheme. Each scheme includes the following fields:

- **`tags`**: A tuple of strings representing the possible tags for the scheme. Tags serve two purposes:
  1. **User hints**: Displayed in the fzf interface to help users understand the type of link.
  2. **Post-processing rules**: Used internally by the plugin to determine the appropriate action based on the selected tag.
- **`opener`**: Specifies the application or process used to open the link (e.g., a browser, editor, or custom process).
- **`regex`**: A regular expression that matches the target pattern.
- **`pre_handler`**: A function that processes the match and returns a dictionary containing:
  - `display_text`: The text displayed in the fzf interface.
  - `tag`: One of the tags defined in `tags`.
  If the match is invalid or false-positive, the `pre_handler` can return `None` to drop the match.
- **`post_handler`**: A function that determines the command to execute for the selected link.

Here’s an example of the updated structure:

```python
default_schemes = [
    {
        "tags": ("url",),
        "opener": OpenerType.BROWSER,
        "regex": re.compile(r"https?://[^\s]+"),
        "pre_handler": lambda m: {
            "display_text": f"{colors.rgb_color(200,0,255)}{m.group(0)}{colors.reset_color}",
            "tag": "url"
        },
        "post_handler": None,
    },
    {
        "tags": ("file", "dir"),
        "opener": OpenerType.CUSTOM,
        "regex": re.compile(r"(\'(?P<link1>\~?[a-zA-Z0-9_\/\-\:\. ]+)\'|(?P<link2>\~?[a-zA-Z0-9_\/\-\:\.]+))"),
        "pre_handler": file_pre_handler,
        "post_handler": file_post_handler,
    },
]
```

### Customizing Pre-Handlers

The `pre_handler` processes matches before they are displayed in the fzf interface. It must return a dictionary with:

- **`display_text`**: A string containing the formatted text for fzf, including colors if configured.
- **`tag`**: A string that must be one of the scheme's `tags`.

#### Dropping False Positives

To handle false positives, the `pre_handler` can return `None`. For example:

```python
def code_error_pre_handler(match: re.Match[str]) -> PreHandledMatch | None:
    resolved_path = heuristic_find_file(match.group("file"))
    if resolved_path is None:
        return None  # Drop the match if the file cannot be resolved

    return {
        "display_text": f"{colors.rgb_color(255,0,0)}{match.group('file')}, line {match.group('line')}{colors.reset_color}",
        "tag": "Python",
    }
```
In this example, matches are dropped if the file path cannot be resolved.

#### Dynamic Tag Assignment

Dynamic tag assignment allows `pre_handler` to adjust tags based on the match content. For example:

- Python vs. generic coding errors:
  ```python
  resolved_path = heuristic_find_file(match.group("file"))
  suffix = resolved_path.suffix
  tag = "Python" if suffix == ".py" else "code err."
  ```

- Files vs. directories:
  ```python
  tag = "dir" if resolved_path.is_dir() else "file"
  ```

#### Disabling Default Schemes

You can disable specific default schemes by populating the `rm_default_schemes` list in your `user_schemes.py` file. For example:

```python
# Remove default schemes (e.g., ["file"] to remove tag "file")
rm_default_schemes: list[str] = ["file", "dir"]
```

When you add a tag to `rm_default_schemes`, all schemes associated with that tag will be disabled. If a scheme has multiple tags, specifying any one of them will disable the entire scheme. **It is not possible to disable just one tag from a multi-tag scheme while keeping other tags active.**

### Overwriting Default Schemes

You can overwrite existing default schemes by defining a new scheme in `user_schemes.py` with at least one of the tags used in the default scheme. The plugin gives precedence to user-defined schemes over default ones.

### Customizing Post-Handlers

The `post_handler` function determines the command to execute for the selected link. Depending on the `opener`, it can return:

- **A dictionary (`dict[str, str]`)**: When the `opener` is set to `OpenerType.EDITOR` or `OpenerType.BROWSER`, the dictionary must include fields required by the specific opener:
  - For `OpenerType.EDITOR`, the dictionary must include:
    - **`file`**: The fully-resolved file path.
    - **`line`** (optional): The line number to open in the editor.
  - For `OpenerType.BROWSER`, the dictionary must include:
    - **`url`**: The URL to open in the browser.

- **A list of strings (`list[str]`)**: When the `opener` is set to `OpenerType.CUSTOM`, the list contains the arguments directly passed to `subprocess.Popen` for execution. The first element of the list must specify the path to the custom opener executable.

#### Example: Handling URLs

For a browser opener, the `post_handler` can return a dictionary with the `url` field:

```python
def ip_post_handler(match: re.Match[str]) -> dict[str, str]:
    ip_addr_str = match.group("ip")
    return {"url": f"https://{ip_addr_str}"}
```

The corresponding scheme:

```python
ip_scheme: SchemeEntry = {
    "tags": ("IPv4",),
    "opener": OpenerType.BROWSER,
    "regex": re.compile(r"[0-9]{1,3}(\.[0-9]{1,3}){3}"),
    "pre_handler": lambda m: {
        "display_text": m.group("ip"),
        "tag": "IPv4"
    },
    "post_handler": ip_post_handler,
}
```

#### Example: Handling Code Errors

For an editor opener, the `post_handler` can return a dictionary with the `file` and `line` fields:

```python
def code_error_post_handler(match: re.Match[str]) -> dict[str, str]:
    file = match.group("file")
    line = match.group("line")

    resolved_path = heuristic_find_file(file)
    if resolved_path is None:
        raise FailedResolvePath(f"Could not resolve the path of: {file}")

    return {"file": str(resolved_path.resolve()), "line": line}
```

The corresponding scheme:

```python
code_error_scheme: SchemeEntry = {
    "tags": ("code err.", "Python"),
    "opener": OpenerType.EDITOR,
    "regex": re.compile(r"File \"(?P<file>...*?)\", line (?P<line>[0-9]+)"),
    "pre_handler": code_error_pre_handler,
    "post_handler": code_error_post_handler,
}
```

#### Example: Handling Files and Directories

For a custom opener, the `post_handler` returns a list of arguments directly passed to `subprocess.Popen`. The first element specifies the custom opener executable:

```python
def file_post_handler(match: re.Match[str]) -> list[str]:
    file_path_str = match.group("link1") or match.group("link2")
    resolved_path = heuristic_find_file(file_path_str)

    if resolved_path is None:
        raise FailedResolvePath(f"Could not resolve the path of: {file_path_str}")

    resolved_path_str = str(resolved_path.resolve())

    if resolved_path.is_file():
        # Use a configured editor to open the file
        return shlex.split(configs.editor_open_cmd.replace("%file", resolved_path_str).replace("%line", "1"))
    else:
        # Open the directory in Finder (macOS), Nautilus (Linux), or Explorer (Windows)
        if sys.platform == "darwin":
            return ["open", "-R", resolved_path_str]
        elif sys.platform == "linux":
            return ["xdg-open", resolved_path_str]
        elif sys.platform == "win32":
            return ["explorer", resolved_path_str]
        else:
            raise NotSupportedPlatform(f"Platform {sys.platform} not supported")
```

The corresponding scheme:

```python
file_scheme: SchemeEntry = {
    "tags": ("file", "dir"),
    "opener": OpenerType.CUSTOM,
    "regex": re.compile(r"(\'(?P<link1>\~?[a-zA-Z0-9_\/\-\:\. ]+)\'|(?P<link2>\~?[a-zA-Z0-9_\/\-\:\.]+))"),
    "pre_handler": file_pre_handler,
    "post_handler": file_post_handler,
}
```

---

### Adding User-Defined Schemes

You can define additional schemes in a file such as `user_schemes.py`. Example:

```python
user_schemes = [
    {
        "tags": ("IPv4",),
        "opener": OpenerType.BROWSER,
        "regex": re.compile(r"[0-9]{1,3}(\.[0-9]{1,3}){3}"),
        "pre_handler": lambda m: {
            "display_text": m.group("ip"),
            "tag": "IPv4"
        },
        "post_handler": ip_post_handler,
    },
]
```

Specify the path to your `user_schemes.py` file in your `.tmux.conf` configuration.

---

## 🤝 Contributing

Contributions are welcome! Please fork this repository and submit a pull request for enhancements or bug fixes, or simply report any issues in the [GitHub repository](https://github.com/alberti42/tmux-fzf-links/issues).

---

## ❤️ Donations

I would be grateful for any donation to support the development of this plugin.

[<img src="images/buy_me_coffee.png" width=300 alt="Buy Me a Coffee QR Code"/>](https://buymeacoffee.com/alberti)

---

## 👨‍💻 Author

- **Author:** Andrea Alberti
- **GitHub Profile:** [alberti42](https://github.com/alberti42)
- **Donations:** [![Buy Me a Coffee](https://img.shields.io/badge/Donate-Buy%20Me%20a%20Coffee-orange)](https://buymeacoffee.com/alberti)

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
