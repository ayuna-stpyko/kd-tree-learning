#!/usr/bin/env python3
"""ジャッジに解答を提出し、結果が出るまで待って表示する。

    python3 submit.py               # solution.py を提出
    python3 submit.py my_answer.py  # ファイルを指定して提出
    python3 submit.py --status 42   # 提出 42 の結果を見る

事前に .env.example を .env にコピーして、NAME (自分の名前) と JUDGE_URL を書いておく。
標準ライブラリだけで動く (Python 3.9 以降)。
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
MAX_BYTES = 65536
WAIT_LIMIT = 600  # 秒

VERDICT_NAMES = {
    "AC": "Accepted",
    "WA": "Wrong Answer",
    "TLE": "Time Limit Exceeded",
    "RE": "Runtime Error",
    "MLE": "Memory Limit Exceeded",
    "OLE": "Output Limit Exceeded",
    "CE": "Compile Error",
    "IE": "Internal Error",
}
PHASE_NAMES = {"correctness": "正誤判定", "score": "スコア計測"}


def die(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def load_env():
    path = os.path.join(HERE, ".env")
    if not os.path.exists(path):
        die(".env がありません。次のようにして作り、名前を書いてください:\n"
            "  cp .env.example .env")
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    name = env.get("NAME", "")
    url = env.get("JUDGE_URL", "").rstrip("/")
    if not NAME_RE.match(name):
        die(".env の NAME が不正です (英数字と _ - のみ、32 文字以内): %r" % name)
    if not url.startswith("http"):
        die(".env の JUDGE_URL が設定されていません")
    return name, url


def request(url, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except ValueError:
            return e.code, {"error": "HTTP %d" % e.code}
    except (urllib.error.URLError, OSError):
        die("ジャッジに接続できません (%s)。\n10.24 のネットワークにつながっているか、"
            ".env の JUDGE_URL が正しいかを確認してください。" % url)


def status_line(st):
    s = st["status"]
    if s in ("new", "queued"):
        ahead = st.get("queue_ahead", 0)
        return "待機中… 前に %d 件" % ahead if ahead else "待機中… まもなく判定します"
    if s == "running":
        p = st.get("progress") or {}
        if p.get("phase") == "correctness":
            return "判定中… 正誤判定 %d/%d" % (p.get("done", 0), p.get("total", 0))
        if p.get("phase") == "score":
            return "判定中… スコア計測 d=%s" % p.get("d") if p.get("d") else "判定中… スコア計測"
        return "判定中… 準備中"
    return ""


def show_result(st, url):
    v = st["verdict"]
    name = VERDICT_NAMES.get(v, v)
    if v == "AC":
        print("Accepted  score %.3fs" % st["score"])
        times = sorted(st.get("score_times", {}).items(), key=lambda x: int(x[0]))
        for i in range(0, len(times), 5):
            print("  " + "  ".join("d=%-2s %.3fs" % (d, t) for d, t in times[i:i + 5]))
        print("順位表: %s/" % url)
        return
    f = st.get("failed")
    where = ""
    if f:
        if f["phase"] == "correctness":
            where = "正誤判定 #%d, D=%d" % (f["index"], f["d"])
        else:
            where = "スコア計測 d=%d" % f["d"]
    msg = st.get("message")
    if v == "CE":
        print("%s\n  %s" % (name, msg or ""))
    else:
        detail = ", ".join(x for x in (where, msg) if x)
        print("%s  (%s)" % (name, detail) if detail else name)
    c = st.get("correctness")
    if c and v != "CE":
        print("  正誤判定: %d/%d 件 AC" % (c["passed"], c["total"]))


def wait_result(url, sid):
    start = time.time()
    last = ""
    tty = sys.stdout.isatty()
    try:
        while True:
            _, st = request("%s/api/submissions/%d" % (url, sid))
            if "error" in st:
                die(st["error"])
            if st["status"] == "done":
                if tty and last:
                    sys.stdout.write("\r" + " " * 40 + "\r")
                show_result(st, url)
                return 0 if st["verdict"] == "AC" else 1
            line = status_line(st)
            if line != last:
                if tty:
                    sys.stdout.write("\r" + line.ljust(40))
                    sys.stdout.flush()
                else:
                    print(line)
                last = line
            if time.time() - start > WAIT_LIMIT:
                print("\n時間がかかっています。結果は後で確認できます:\n  python3 submit.py --status %d" % sid)
                return 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n判定は続いています。結果は次のコマンドで確認できます:\n  python3 submit.py --status %d" % sid)
        return 1


def main():
    args = sys.argv[1:]
    name, url = load_env()
    if args[:1] == ["--status"]:
        if len(args) != 2 or not args[1].isdigit():
            die("使い方: python3 submit.py --status 提出ID")
        sys.exit(wait_result(url, int(args[1])))
    if len(args) > 1 or (args and args[0].startswith("-")):
        die(__doc__.strip())
    path = args[0] if args else os.path.join(HERE, "solution.py")
    if not os.path.isfile(path):
        die("ファイルがありません: %s" % path)
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) > MAX_BYTES:
        die("ファイルが大きすぎます (%d バイト。上限 %d バイト)" % (len(raw), MAX_BYTES))
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError:
        die("ファイルを UTF-8 として読めません")
    if not source.strip():
        die("ファイルが空です")

    code, res = request(url + "/api/submit", {"name": name, "source": source})
    if code != 200:
        die(res.get("error", "提出に失敗しました (HTTP %d)" % code))
    sid = res["id"]
    print("提出しました (名前: %s, ID: %d)" % (name, sid))
    sys.exit(wait_result(url, sid))


if __name__ == "__main__":
    main()
