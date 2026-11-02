import sys


def main():
    data = sys.stdin.buffer.read().split()
    n, d = int(data[0]), int(data[1])
    # 点 i (1-indexed) の座標は points[i - 1]
    points = [list(map(int, data[2 + i * d:2 + (i + 1) * d])) for i in range(n)]
    pos = 2 + n * d
    q = int(data[pos])
    queries = [int(x) for x in data[pos + 1:pos + 1 + q]]

    ans = []
    for i in queries:
        # TODO: 点 i 以外で点 i に最も近い点の番号を求める
        ans.append(1)

    sys.stdout.write("\n".join(map(str, ans)) + "\n")


main()
