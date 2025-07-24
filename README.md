# To build

```bash
# fill in the version number
# update pyproject.toml to the new version
git tag v*.*.*
git push origin v*.*.*
# package is auto-built in GitHub Actions
```

# To install

```bash
# fill in the version number
pip install git+https://github.com/Sefaria/ne_span.git@v*.*.*
```