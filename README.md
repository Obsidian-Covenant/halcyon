# halcyon

## Modernization Covenant

This is a clean-room reimplementation inspired by the original **halcyon** tool, a repository crawler that runs checksums for static files found within a given git repository.

Key changes:

- ✅ Python 3 support

### Installation

#### Dependencies

Runtime dependencies:
```
git python
```

#### From source

```shell
git clone https://github.com/Obsidian-Covenant/halcyon.git
cd halcyon
python halcyon.py
```

### Usage

Generate per-file **MD5 signatures across git history**, labeled by a “version” string extracted from a chosen file in a git repository.

Output is written to `./sigs/` as simple YAML-ish files.

#### What it does

Halcyon:
1. Walks through `git log --stat` history
2. Tracks files that appear in the history (with filters + optional top-N limit)
3. For each tracked file and each commit where it exists, computes:
   `md5( git show <commit>:<file> )`
4. Labels each commit with a “version” extracted from a **single** `check_file` you choose (via regex)
5. Writes results into `sigs/<repo>-<basename>` files

Use a local repository:
```shell
python halcyon.py \
  -u ./my-local-repo \
  -f VERSION \
  -m "^([0-9]+(?:\.[0-9]+)+)" \
  --omit-directory "docs,vendor" \
  -t 10
```

Use a remote git repository:
```shell
python halcyon.py \
  -c \
  -u https://github.com/foo/bar \
  -f VERSION \
  -m "^([0-9]+(?:\.[0-9]+)+)" \
  --omit-directory "docs,vendor" \
  -t 10
```

Halcyon writes to `./sigs/` (created if missing). Each output file is named:
```
sigs/<app_name>-<basename>
```
Contents look like:
```yaml
---
config:
  app_name: ./bar
  check_file: packages/PKGBUILD
sigs:
  12.0-commitid-<commit_sha>: <md5_hash>
  12.1-commitid-<commit_sha>: <md5_hash>
```
Each entry under sigs: represents the MD5 hash of that file’s content at a specific commit.
If the hash changes, the file changed.

#### Notes / Gotchas

* The `--file` you use for version extraction must be present in the git history (committed), not just in your working tree.
* Regex patterns should usually be quoted to prevent shell escaping issues.
* `--omit-directory` is a simple substring/regex match against file paths. Use carefully.