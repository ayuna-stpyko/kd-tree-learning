#!/usr/bin/env python3
"""ジャッジに解答を提出し、結果が出るまで待って表示する。

    python3 submit.py               # solution.py を提出
    python3 submit.py my_answer.py  # ファイルを指定して提出
    python3 submit.py --problem 1             # 練習問題 practice/1/solution.py を提出
    python3 submit.py --problem 1 my_1d.py    # 練習問題にファイルを指定して提出
    python3 submit.py --status 42   # 提出 42 の結果を見る

--problem: 省略すると本問題 (kd-tree)。1 = 練習問題 1 次元、2 = 練習問題 2 次元マンハッタン距離 (順位表には載らない)

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
NAME_MAX_LEN = 32
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,%d}$" % NAME_MAX_LEN)
MAX_SOURCE_BYTES = 65536  # ジャッジ側の上限と同じ
WAIT_LIMIT_SEC = 600  # これより長く待ったら、後で --status で見るよう案内して終わる
POLL_SEC = 1
HTTP_TIMEOUT_SEC = 15
STATUS_WIDTH = 40  # 状況の表示を上書きするときの幅
TIMES_PER_LINE = 5  # 次元ごとの時間を 1 行に何個並べるか
CORRECTNESS, SCORE = "correctness", "score"
MAIN_PROBLEM = "kdtree-nn"
# 練習問題: --problem に指定する番号 -> (ジャッジでの問題 ID, ディレクトリ)
PRACTICE_PROBLEMS = {
    "1": ("nn-1d", "practice/1"),
    "2": ("nn-2d-l1", "practice/2"),
}
PHASE_NAMES = {CORRECTNESS: "正誤判定", SCORE: "スコア計測"}


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
        die(".env の NAME が不正です (英数字と _ - のみ、%d 文字以内): %r" % (NAME_MAX_LEN, name))
    if not url.startswith("http"):
        die(".env の JUDGE_URL が設定されていません")
    return name, url


def request(url, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as r:
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
        phase = PHASE_NAMES.get(p.get("phase"))
        if phase is None:
            return "判定中… 準備中"
        if p["phase"] == CORRECTNESS:
            return "判定中… %s %d/%d" % (phase, p.get("done", 0), p.get("total", 0))
        return "判定中… %s d=%s" % (phase, p["d"]) if p.get("d") else "判定中… " + phase
    return ""


def show_result(st, url):
    v = st["verdict"]
    name = st.get("verdict_name", v)
    if v == "AC" and st.get("score") is None:  # 練習問題 (スコアなし)
        c = st.get("correctness") or {}
        print("Accepted  (%d/%d 件 AC)" % (c.get("passed", 0), c.get("total", 0)))
        return
    if v == "AC":
        print("Accepted  score %.3fs" % st["score"])
        times = sorted(st.get("score_times", {}).items(), key=lambda x: int(x[0]))
        for i in range(0, len(times), TIMES_PER_LINE):
            print("  " + "  ".join("d=%-2s %.3fs" % (d, t) for d, t in times[i:i + TIMES_PER_LINE]))
        print("順位表: %s/" % url)
        return
    f = st.get("failed")
    where = ""
    if f:
        phase = PHASE_NAMES.get(f["phase"], f["phase"])
        if f["phase"] == CORRECTNESS:
            where = "%s #%d, D=%d" % (phase, f["index"], f["d"])
        else:
            where = "%s d=%d" % (phase, f["d"])
    msg = st.get("message")
    if v == "CE":
        print("%s\n  %s" % (name, msg or ""))
    else:
        detail = ", ".join(x for x in (where, msg) if x)
        print("%s  (%s)" % (name, detail) if detail else name)
    c = st.get("correctness")
    if c and v != "CE":
        print("  %s: %d/%d 件 AC" % (PHASE_NAMES[CORRECTNESS], c["passed"], c["total"]))


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
                    sys.stdout.write("\r" + " " * STATUS_WIDTH + "\r")
                show_result(st, url)
                return 0 if st["verdict"] == "AC" else 1
            line = status_line(st)
            if line != last:
                if tty:
                    sys.stdout.write("\r" + line.ljust(STATUS_WIDTH))
                    sys.stdout.flush()
                else:
                    print(line)
                last = line
            if time.time() - start > WAIT_LIMIT_SEC:
                print("\n時間がかかっています。結果は後で確認できます:\n  python3 submit.py --status %d" % sid)
                return 1
            time.sleep(POLL_SEC)
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
    problem, base, shown = MAIN_PROBLEM, HERE, ""
    if args[:1] == ["--problem"]:
        if len(args) < 2 or args[1] not in PRACTICE_PROBLEMS:
            die("--problem には 1 (1 次元) か 2 (2 次元マンハッタン距離) を指定してください")
        problem, sub = PRACTICE_PROBLEMS[args[1]]
        base = os.path.join(HERE, sub)
        shown = ", 練習問題 %s" % args[1]
        args = args[2:]
    if len(args) > 1 or (args and args[0].startswith("-")):
        die(__doc__.strip())
    path = args[0] if args else os.path.join(base, "solution.py")
    if not os.path.isfile(path):
        die("ファイルがありません: %s" % path)
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) > MAX_SOURCE_BYTES:
        die("ファイルが大きすぎます (%d バイト。上限 %d バイト)" % (len(raw), MAX_SOURCE_BYTES))
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError:
        die("ファイルを UTF-8 として読めません")
    if not source.strip():
        die("ファイルが空です")

    code, res = request(url + "/api/submit", {"name": name, "problem": problem, "source": source})
    if code != 200:
        die(res.get("error", "提出に失敗しました (HTTP %d)" % code))
    sid = res["id"]
    print("提出しました (名前: %s, ID: %d%s)" % (name, sid, shown))
    sys.exit(wait_result(url, sid))


if __name__ == "__main__":
    main()
