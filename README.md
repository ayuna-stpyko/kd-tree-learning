# 最近傍点(KD-tree)

## 問題

$N$ 人の人が $D$ 次元空間上にいます。 $i$ 人目の座標は $(X_{i,1}, X_{i,2}, \dots, X_{i,D})$ です。 $Q$ 個クエリが与えられるので、それぞれに答えてください。

$Q$ 個のクエリに答えてください。各クエリでは番号 $m_i$ が与えられるので、人 $m_i$ 以外の人のうち、人 $m_i$ にユークリッド距離で最も近い人の番号を出力してください。最も近い人が複数あるときは、そのうち**番号が最小の人**を出力してください。

人 $a$ と人 $b$ のユークリッド距離は $\sqrt{\sum_{k=1}^{D} (X_{a,k} - X_{b,k})^2}$ です。

### 入力

```
N D
X_1,1 X_1,2 ... X_1,D
...
X_N,1 X_N,2 ... X_N,D
Q
m_1
...
m_Q
```

### 出力

$Q$ 行出力してください。 $i$ 行目には、クエリ $m_i$ の答えの番号を出力してください。

### 制約

- $2 \leq N$
- $1 \leq D \leq 10$
- $N \times D \leq 2 \times 10^5$
- $|X_{i,k}| \leq 10^8$
- $1 \leq Q \leq N$
- $1 \leq m_i \leq N$
- 入力はすべて整数

### 入出力例

入力 (`samples/01.in`)

```
6 2
0 0
2 0
0 2
2 0
-1 -1
5 5
6
1
2
3
4
5
6
```

出力 (`samples/01.out`)

```
5
4
1
2
1
2
```

- 人 2 と人 4 は同じ座標なので、互いに相手が答えになります。
- 人 6 から見ると、人 2・人 3・人 4 がどれも距離 $\sqrt{34}$ で最も近いので、番号が最小の 2 が答えです。

## 解き方の決まり

- 提出するのは Python のファイル 1 つです。標準入力から読み、標準出力に書いてください。
- 制限時間は 1 ケース 2 秒です。
- 使える文法は Python 3.11 までです。
- numpy や scipy などの外部ライブラリは使えません (標準ライブラリのみ)。
- 答えが合っていれば、どんな方法で解いても構いません。
- 手元とジャッジでは実行時間が異なります。

## 準備

```bash
cp .env.example .env
```

`.env` を開き、`NAME` を自分の名前 (英数字と `_` `-` のみ、32 文字以内) にしてください。`JUDGE_URL` は運営から案内されたものにしてください。

## 手元で試す

`solution.py` に解答を書き、`samples/` のケースで確認できます。

```bash
python3 local_judge.py
```

別のファイルを試すときは `python3 local_judge.py ファイル名` です。

## 提出する

```bash
python3 submit.py
```

`solution.py` が提出され、判定が終わるまで待って結果を表示します。別のファイルを提出するときは `python3 submit.py ファイル名` です。

- 同じ名前での提出は 30 秒に 1 回までです。
- 待っている途中で Ctrl+C で抜けても判定は続きます。結果は `python3 submit.py --status 提出ID` で確認できます。

### 判定結果

| 結果 | 意味 |
|---|---|
| Accepted (AC) | 正解 |
| Wrong Answer (WA) | 答えが違う |
| Time Limit Exceeded (TLE) | 2 秒以内に終わらなかった |
| Runtime Error (RE) | 実行中にエラーで止まった |
| Memory Limit Exceeded (MLE) | メモリを使いすぎた |
| Output Limit Exceeded (OLE) | 出力が多すぎる |
| Compile Error (CE) | 文法エラー |

## 練習問題

kd-tree に入る前の練習として、判定だけが返る問題があります (順位表には載りません。提出間隔の制限は本問題と共通です)。

| `--problem` | 内容 | 問題文 |
|---|---|---|
| `1` | 1 次元の最近傍点 | [practice/1/README.md](practice/1/README.md) |
| `2` | 2 次元の最近傍点 (マンハッタン距離) | [practice/2/README.md](practice/2/README.md) |

`--problem` で問題の番号を指定します。ファイルを省略すると、その問題のディレクトリの `solution.py` (例: `practice/1/solution.py`) を使います。

```bash
python3 local_judge.py --problem 1
python3 submit.py --problem 1
```

## 順位表

`JUDGE_URL` をブラウザで開くと見られます。
