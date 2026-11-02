"""Case-insensitive asset path resolution for project imports.

The MUGEN packs ship DEF files whose `sprite`/`anim` names often differ in
case from the files on disk (`Mary.sff` vs `mary.sff`, `choi01.act` vs
`choi01.ACT`).  This is harmless on Windows but breaks the build on a
case-sensitive filesystem.  Resolve each path component by exact match
first, then by a case-insensitive directory scan.
"""
import os


def resolve(root, rel):
    """Return an absolute path for *rel*, matching component case if needed.

    ``root`` is the project root used for relative paths.  Existing paths
    are returned unchanged.  If a component is missing under its exact name,
    the first case-insensitive match in that directory is used.
    """
    if not rel:
        return rel
    rel = os.fspath(rel)
    if os.path.isabs(rel):
        return _resolve_abs(rel)

    cur = os.fspath(root)
    for part in rel.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        exact = os.path.join(cur, part)
        if os.path.exists(exact):
            cur = exact
            continue
        try:
            names = os.listdir(cur)
        except OSError:
            return os.path.join(os.fspath(root), rel)
        match = next((name for name in names
                      if name.lower() == part.lower()), None)
        if match is None:
            return os.path.join(os.fspath(root), rel)
        cur = os.path.join(cur, match)
    return cur


def _resolve_abs(path):
    if os.path.exists(path):
        return path
    cur = os.path.sep
    for part in path.strip(os.path.sep).split(os.path.sep):
        exact = os.path.join(cur, part)
        if os.path.exists(exact):
            cur = exact
            continue
        try:
            names = os.listdir(cur)
        except OSError:
            return path
        match = next((name for name in names
                      if name.lower() == part.lower()), None)
        if match is None:
            return path
        cur = os.path.join(cur, match)
    return cur
