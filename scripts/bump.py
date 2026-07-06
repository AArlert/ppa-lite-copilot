#!/usr/bin/env python3
# 版本号管理：0.M.P（M = Milestone，对应 spec 的 Lab；P = 里程碑内迭代）
# 用法: bump.py            → patch +1（同一里程碑内打磨）
#       bump.py minor      → 进入下一个 Milestone（0.M+1.0）
#       bump.py 0.3.2      → 显式指定
import json
import re
import sys
from pathlib import Path

VERSION_JSON = Path(__file__).resolve().parent.parent / "version.json"
SEMVER_RE = re.compile(r"^0\.(\d+)\.(\d+)$")


def main():
    data = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
    cur = data["version"]
    m = SEMVER_RE.match(cur)
    if not m:
        sys.exit(f"当前版本号非法: {cur}")
    major, patch = int(m.group(1)), int(m.group(2))

    arg = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if arg == "patch":
        new = f"0.{major}.{patch + 1}"
    elif arg == "minor":
        new = f"0.{major + 1}.0"
    elif SEMVER_RE.match(arg):
        new = arg
    else:
        sys.exit(f"参数非法: {arg}（可用: patch / minor / 0.M.P）")

    new_m = SEMVER_RE.match(new)
    data["version"] = new
    data["milestone"] = f"M{new_m.group(1)}"
    VERSION_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{cur} → {new} ({data['milestone']})")
    print("提醒: 收尾时同步 status.jsonl 首行版本；里程碑完成时打 tag: git tag v" + new)


if __name__ == "__main__":
    main()
