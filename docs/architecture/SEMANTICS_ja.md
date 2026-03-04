# SEMANTICS（意味論仕様）

本ドキュメントは `verified-json-reference-parser` の意味論契約を定義する。

本ライブラリの意味論コアは以下を満たすことを目的とする。

* 小さい
* 明示的
* 決定的
* 機械検証可能
* 一度固定されたら安定する

本仕様は Phase 1 における規範的定義である。

---

# 1. ドメインモデル

## 1.1 JSON 値

JSON 値は以下から構成される。

* `null`
* boolean
* number
* string
* array
* object

object は有限な文字列キーから JSON 値への写像とする。
array は有限な順序付き JSON 値列とする。

---

## 1.2 Pointer 表現

内部表現は以下とする。

```
Pointer := readonly string[]
```

空文字列ポインタ `""` は

```
[]
```

で表され、ドキュメント全体を指す。

---

# 2. Result 型

すべての意味論的操作は明示的な `Result<T>` を返す。

```
Result<T> :=
  | { ok: true; value: T }
  | { ok: false; kind: "InvalidPointer" }
  | { ok: false; kind: "TypeMismatch" }
  | { ok: false; kind: "NotFound" }
```

## 2.1 エラー分類

### InvalidPointer

* ポインタ文字列の構文が不正
* 未対応の参照形式
* 不正なエスケープ

### TypeMismatch

* プリミティブ値に対してトークンを適用した
* 配列に対して非数値トークンを適用した
* 配列走査時に配列インデックストークン形式が不正

### NotFound

* パスは適用可能だが、該当するキー／要素が存在しない

## 2.2 設計保証

* `undefined` は返さない
* 例外を投げない
* 失敗は常に明示される
* 同一入力は常に同一結果を返す

---

# 3. JSON Pointer 意味論（RFC 6901）

## 3.1 構文

ポインタ文字列は以下のいずれか。

* `""`（空文字列）
* `/` で始まり `/` で区切られたセグメント列

例：

```
/a/b/0
```

これに違反する場合は `InvalidPointer`。

---

## 3.2 エスケープ規則

### エスケープ

* `~` → `~0`
* `/` → `~1`

### アンエスケープ

* `~1` → `/`
* `~0` → `~`

その他の `~` パターンは `InvalidPointer`。

---

## 3.3 parsePointer

```
parsePointer(pointerString) -> Result<Pointer>
```

規則：

1. `pointerString === ""` の場合

   ```
   { ok: true, value: [] }
   ```

2. それ以外

   * `/` で始まらなければ `InvalidPointer`
   * `/` で分割
   * 各セグメントをアンエスケープ
   * 不正なエスケープがあれば `InvalidPointer`

---

## 3.4 formatPointer

```
formatPointer(pointer) -> string
```

規則：

* `[]` → `""`
* それ以外

  * 各トークンをエスケープ
  * `/` で連結
  * 先頭に `/` を付与

---

# 4. Pointer 評価意味論

## 4.1 get

```
get(doc, pointer) -> Result<JSONValue>
```

評価はトークンを左から順に適用する。

---

## 4.2 Object の場合

現在値が object の場合：

* トークン文字列と完全一致するキーを選択
* 存在しない場合 → `NotFound`

---

## 4.3 Array の場合

現在値が array の場合、トークンは配列インデックスとして解釈される。

### インデックストークンの条件

トークンは以下を満たす必要がある。

* 10進数字のみで構成される
* `"0"` を除き、先頭ゼロを持たない

有効例：

* `"0"`
* `"1"`
* `"42"`

無効例：

* `"01"`（先頭ゼロ）
* `"-1"`
* `"1.0"`
* `"foo"`

条件を満たさない場合 → `TypeMismatch`

数値として有効だが範囲外の場合 → `NotFound`

---

## 4.4 Primitive の場合

現在値がプリミティブ（null / boolean / number / string）の場合：

* 追加トークンがあれば → `TypeMismatch`

---

# 5. ローカル JSON Reference 意味論

## 5.1 resolveLocalRef

```
resolveLocalRef(doc, refString) -> Result<JSONValue>
```

対応形式（Phase 1）：

* `"#"` → ドキュメント全体
* `"#/..."` → JSON Pointer として評価

規則：

1. `refString === "#"`

   ```
   { ok: true, value: doc }
   ```

2. `"#/"` で始まる場合

   * `#` 以降を JSON Pointer として解釈
   * parse → get

3. それ以外

   ```
   { ok: false, kind: "InvalidPointer" }
   ```

外部参照（例：`other.json#/x`）は Phase 1 では未対応。

---

# 6. 検証対象不変条件

以下の不変条件は、適用可能な範囲では Rocq により機械検証され、実装に対しては Z3 ベースのオラクルを含む差分検証で継続的に確認されることを意図する。

1. エスケープ往復性

   ```
   unescape(escape(x)) = x
   ```

2. ポインタ往復性

   ```
   parsePointer(formatPointer(ptr)).value = ptr
   ```

3. 決定性
   同一入力は常に同一結果を返す

4. 暗黙的補正なし

   * 数値正規化を行わない
   * 暗黙フォールバックを行わない

---

# 7. 非目標

本仕様は以下を定義しない。

* JSON Schema キーワード意味論
* 外部参照取得
* ネットワーク処理
* RFC 3986 の完全意味論
* URI 正規化規則

---

# 8. 安定性方針

意味論コアが形式的に固定された後は、

* 振る舞いを暗黙に変更しない
* 変更は明示的に文書化する
* 回帰テストで保証する

意味論の安定性を最優先とする。

---

