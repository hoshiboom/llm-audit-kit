# VHS tape for llm-audit-kit demo GIF.
#
# Prereq:
#   Install VHS: https://github.com/charmbracelet/vhs
#   macOS:  brew install vhs
#   Linux:  go install github.com/charmbracelet/vhs@latest
#   Windows (scoop): scoop install vhs
#
# Render:
#   vhs docs/demo.tape
#
# Output:
#   docs/demo.gif   (referenced in README)

Output docs/demo.gif

Set Shell bash
Set FontSize 16
Set Width 1100
Set Height 620
Set TypingSpeed 55ms
Set Theme "Dracula"

# Header
Type "# llm-audit-kit — a layered LLM app security audit CLI"
Sleep 1s
Enter

# cd into the tool
Type "cd tools/llm-audit"
Enter
Sleep 500ms

# Show zero deps
Type "# zero-dependency: only stdlib Python 3.8+"
Enter
Type "python --version"
Enter
Sleep 800ms

# List L3 items
Type "python audit.py --non-interactive --layer L3"
Enter
Sleep 2500ms

# Run with sample answers, render report
Type "python audit.py --answers example-answers.json --output /tmp/report.md"
Enter
Sleep 3500ms

# Show report head
Type "head -30 /tmp/report.md"
Enter
Sleep 3000ms

Type "# Star the repo if you find it useful: github.com/hoshiboom/llm-audit-kit"
Sleep 2000ms
