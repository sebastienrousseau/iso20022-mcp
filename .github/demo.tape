Output .github/demo.gif

Set FontSize 14
Set Width 1200
Set Height 600
Set Padding 20
Set Theme "Catppuccin Mocha"

Type "poetry run iso20022-mcp --help"
Sleep 500ms
Enter
Sleep 2s

Type "poetry run python -c 'import iso20022_mcp.server as s; print(s.list_families())'"
Sleep 500ms
Enter
Sleep 3s
