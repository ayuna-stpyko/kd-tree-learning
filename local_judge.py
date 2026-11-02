#!/usr/bin/env python3
"""samples/ のケースで解答を実行し、正しいかどうかと実行時間を表示する。

    python3 local_judge.py               # solution.py を確認
    python3 local_judge.py my_answer.py  # ファイルを指定

手元の python3 で動かす。ジャッジとは実行環境が違うので、時間は目安。
標準ライブラリだけで動く (Python 3.9 以降)。
"""
import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TIME_LIMIT = 2.0  # ジャッジと同じ 1 ケースの制限時間
PREVIEW_TOKENS = 20  # WA のとき、期待と出力を先頭から何個まで見せるか


def preview(tokens):
    return b" ".join(tokens[:PREVIEW_TOKENS]).decode("utf-8", "replace")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "solution.py")
    if not os.path.isfile(path):
        sys.exit("ファイルがありません: %s" % path)
    cases = sorted(glob.glob(os.path.join(HERE, "samples", "*.in")))
    if not cases:
        sys.exit("samples/ にケースがありません")

    passed = 0
    for inp in cases:
        name = os.path.basename(inp)[:-3]
        with open(inp, "rb") as f:
            data = f.read()
        with open(inp[:-3] + ".out", "rb") as f:
            expected = f.read().split()
        t0 = time.perf_counter()
        try:
            p = subprocess.run([sys.executable, path], input=data, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=TIME_LIMIT)
        except subprocess.TimeoutExpired:
            print("%-6s TLE  (%.1f 秒を超えました)" % (name, TIME_LIMIT))
            continue
        elapsed = time.perf_counter() - t0
        if p.returncode != 0:
            print("%-6s RE   %.3fs" % (name, elapsed))
            sys.stdout.write(p.stderr.decode("utf-8", "replace"))
            continue
        got = p.stdout.split()
        if got == expected:
            passed += 1
            print("%-6s AC   %.3fs" % (name, elapsed))
        else:
            print("%-6s WA   %.3fs" % (name, elapsed))
            print("  期待: %s" % preview(expected))
            print("  出力: %s" % preview(got))
    print("\n%d/%d 件 AC" % (passed, len(cases)))
    sys.exit(0 if passed == len(cases) else 1)


if __name__ == "__main__":
    main()
