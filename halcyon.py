#!/usr/bin/env python3
import os, re, hashlib, argparse, operator
from subprocess import run, PIPE

def parse_show(commit, search_file):
    p = run(["git", "show", f"{commit}:{search_file}"], stdout=PIPE, stderr=PIPE, text=True)
    if p.returncode != 0:
        return ""
    return p.stdout

def parse_log(search_file, string, omit_directory, top):
    p = run(["git", "log", "--stat", "--stat-width=10000", "--pretty=oneline", "--format=\x11%H\x12"],
            stdout=PIPE, stderr=PIPE, text=True)
    log = p.stdout

    files = {}
    commits = []
    version = {}
    changed = 0
    commit = ""
    current_version = ""

    for i in log.splitlines():
        if re.match(r"\x11.*\x12", i):
            if changed == 0:
                version[commit] = current_version
            changed = 0
            commit = re.sub(r"[\x11\x12]", "", i)
            commits.append(commit)

        elif "|" in i:
            file = i.split()[0]
            if file == search_file:
                try:
                    m = re.search(string, parse_show(commit, search_file))
                    if m:
                        current_version = "-".join(m.groups()) + "-commitid-" + commit
                        version[commit] = current_version
                        changed = 1
                except re.error:
                    pass
            else:
                files.setdefault(file, {}).setdefault(commit, None)

    # filter
    tmp = {}
    for file in files:
        if re.match(r"^.*\.(php|asp|xml|sql|ini)$", file):
            continue
        if omit_directory and re.search(omit_directory, file):
            continue
        tmp[file] = files[file]
    files = tmp

    # top N (sort by number of commits per file)
    if top != 0:
        files = dict(sorted(files.items(), key=lambda kv: len(kv[1]), reverse=True)[:top])

    # hash file contents at each commit
    for file in files:
        for commit in list(files[file].keys()):
            p = run(["git", "show", f"{commit}:{file}"], stdout=PIPE, stderr=PIPE)
            if p.returncode != 0:
                continue
            files[file][commit] = hashlib.md5(p.stdout).hexdigest()

    return files, commits, version

def clone(url):
  path = url.rstrip("/").split("/")[-1].split(".")[0]

  if os.path.isdir(path) and os.path.isdir(os.path.join(path, ".git")):
    # repo already exists: update it
    os.chdir(path)
    run(["git", "fetch", "--all", "--prune"], check=True)
    run(["git", "pull", "--ff-only"], check=False)  # don't crash if detached, etc.
    return path

  # fresh clone
  run(["git", "clone", url], check=True)
  os.chdir(path)
  return path

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-c", "--clone", help="Clone the repo first.", action="store_true")
  parser.add_argument("-u", "-p", "--url", "--path", help="Path or URL to the repository.", required=True)
  parser.add_argument("-f", "--file", help="File to search", required=True)
  parser.add_argument("-m", "--match", help="Regex to match line with version number (i.e., '^\\\\\\$wp_version = \\x27([^']+)\\x27;$')", required=True)
  parser.add_argument("--omit-directory", help="Comma separated list of directories to omit.", default="")
  parser.add_argument("-t", "--top", help="Top 'n' files to use. (0 for unlimited)", default=10, type=int)
  args=parser.parse_args()

  if args.clone:
    print("Cloning: %s" % args.url)
    path = clone(args.url)
  else:
    os.chdir(args.url)
    path = args.url

  omit_re = None
  if args.omit_directory.strip():
    omit_re = "(" + "|".join(map(re.escape, args.omit_directory.split(","))) + ")"

  (files, commits, version) = parse_log(args.file, args.match, omit_re, args.top)

  os.chdir("..")

  try:
    os.stat("sigs")
  except:
    os.mkdir("sigs")

  for file in files:
    f = open("sigs/%s-%s" % (path, file.rstrip("/").split("/")[-1]), "w")
    f.write("---\n")
    f.write("config:\n")
    f.write("  app_name: " + path + "\n")
    f.write("  check_file: " + file + "\n")
    f.write("sigs:\n")
    for revision in files[file]:
      try:
        f.write("  " + version[revision] + ": " + files[file][revision] + "\n")
      except:
        pass
    f.close()
