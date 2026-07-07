#!/usr/bin/env python3
# 版本号管理：0.M.P（M = Milestone；P = 里程碑内迭代）
# 用法: bump.py            → patch +1（同一里程碑内打磨）
#       bump.py minor      → 进入下一个 Milestone（0.M+1.0）
#       bump.py 0.3.2      → 显式指定
# bump 后自动在 status.jsonl / log.md 顶部插入 TODO 骨架（date/version 由脚本写死，
# agent 只填语义；docs-check 会拦截未填写的 TODO）——机械交脚本、语义留 Agent。
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_JSON = ROOT / "version.json"
STATUS = ROOT / "doc" / "status.jsonl"
LOG = ROOT / "doc" / "log.md"
SEMVER_RE = re.compile(r"^0\.(\d+)\.(\d+)$")

LOG_SKELETON = """## [{ver}] {today} TODO（一句话标题）

**做了什么**
- TODO

**没做什么**
- TODO

**下一步**
- TODO

**如何验证**
- TODO

"""


def insert_skeletons(ver):
    today = date.today().isoformat()
    # status.jsonl：首行插入骨架（若首行已是该版本则不重复插）
    lines = [l for l in STATUS.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines or json.loads(lines[0]).get("version") != ver:
        rec = {"date": today, "version": ver, "summary": "TODO"}
        lines.insert(0, json.dumps(rec, ensure_ascii=False))
        STATUS.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("status.jsonl: 已插入骨架首行（summary 待填）")
    # log.md：文件头之后、第一个块之前插入骨架块（块头只认行首 "## ["，避免命中头部说明文字）
    text = LOG.read_text(encoding="utf-8")
    if not re.search(rf"^## \[{re.escape(ver)}\]", text, flags=re.M):
        block = LOG_SKELETON.format(ver=ver, today=today)
        m = re.search(r"^## \[", text, flags=re.M)
        text = text[:m.start()] + block + text[m.start():] if m else text.rstrip() + "\n\n" + block
        LOG.write_text(text, encoding="utf-8")
        print("log.md: 已插入骨架块（四问待填）")


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
    insert_skeletons(new)
    print("提醒: 填完骨架跑 make docs-check；里程碑完成时打 tag: git tag v" + new)


if __name__ == "__main__":
    main()
