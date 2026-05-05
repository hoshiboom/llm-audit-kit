# docs/

Supporting assets for the project.

## Files

- `demo.tape` — [VHS](https://github.com/charmbracelet/vhs) script that
  records the main README demo GIF.
- `demo.gif` — generated output. Committed so GitHub README can display it.

## Regenerate the demo GIF

```bash
# one-time setup (pick the one for your OS)
brew install vhs          # macOS
scoop install vhs         # Windows
go install github.com/charmbracelet/vhs@latest

# render
cd <repo-root>
vhs docs/demo.tape
# -> produces docs/demo.gif
```

Then uncomment the `![demo](docs/demo.gif)` line in the main README.
