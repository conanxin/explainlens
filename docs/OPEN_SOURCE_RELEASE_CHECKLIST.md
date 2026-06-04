# Open Source Release Checklist

Before publishing to GitHub, verify the following:

## Code Quality

- [ ] All tests pass: `python -m pytest`
- [ ] No linter warnings (optional but recommended)
- [ ] Code is formatted consistently

## Security

- [ ] No API keys committed (`grep -r "sk-" .` returns nothing in tracked files)
- [ ] No passwords or secrets in source code
- [ ] No private data in example files
- [ ] `.env` is in `.gitignore`

## Documentation

- [ ] README.md is complete and accurate
- [ ] LICENSE file exists (MIT)
- [ ] CONTRIBUTING.md explains contribution workflow
- [ ] SECURITY.md covers key concerns
- [ ] ROADMAP.md reflects current and future plans

## Examples

- [ ] Sample input files work correctly
- [ ] Example command in README runs successfully
- [ ] Sample outputs look reasonable

## Repository

- [ ] `git status` is clean (no untracked files that should be committed)
- [ ] `.gitignore` covers build artifacts, venv, IDE files
- [ ] Commit messages are meaningful

## GitHub

- [ ] Repository name: `explainlens`
- [ ] Description: "Turn papers and complex texts into visual explainer cards and cartoon storyboards."
- [ ] Topics added: python, education, visualization, nlp, explainer
- [ ] About section populated
