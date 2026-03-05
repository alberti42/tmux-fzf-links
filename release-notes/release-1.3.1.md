# Change log

# Fixes

- Improved handling multiple alternative regex in a scheme. **This is a breaking change requiring the field `regex` in the schmes to be a list of regex instead of a single regex.** For most applications, a list containing a single regex is sufficient. Use multiple regex to match alternatives.
