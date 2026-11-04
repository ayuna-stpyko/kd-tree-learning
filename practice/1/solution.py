# 入力の読み込み
n, d = map(int, input().split())
points = [list(map(int, input().split())) for _ in range(n)]
q = int(input())
queries = [int(input()) for _ in range(q)]

for i in queries:
    # TODO: 点 i 以外で点 i に最も近い点の番号を求める
    ans = # 答え
    print(ans)
