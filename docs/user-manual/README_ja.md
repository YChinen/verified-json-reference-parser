# ユーザーマニュアル

このマニュアルは、`verified-json-reference-parser` を JSON Pointer および
ローカル JSON Reference 処理のための、小さく決定的なコアとして利用したい
アプリケーション開発者向けです。

Phase 1 の対象範囲:

* JSON Pointer の parse / format
* JSON 値に対する pointer 評価
* `#` および `#/...` のローカル JSON Reference 解決

Phase 1 の対象外:

* 外部参照の取得
* RFC 3986 に基づく URI 解決
* JSON Schema 全体の検証

English version: [README.md](./README.md)

---

## 1. このライブラリが提供するもの

公開 API は意図的に小さく保たれています。

* `parsePointer(pointerString)`
* `formatPointer(pointer)`
* `get(doc, pointer)`
* `resolveLocalRef(doc, refString)`

コア操作はすべて次の性質を持ちます。

* 純粋関数である
* 決定的である
* `Result<T>` により失敗を明示する

コア API は意味論上の失敗を throw しません。代わりに次のいずれかを返します。

* `{ ok: true, value: ... }`
* `{ ok: false, kind: "InvalidPointer" }`
* `{ ok: false, kind: "TypeMismatch" }`
* `{ ok: false, kind: "NotFound" }`

---

## 2. インストール

```bash
npm install verified-json-reference-parser
```

このパッケージは、JSON Schema ツールや、安定した参照処理が必要なコードへ
組み込むために設計されています。

---

## 3. 基本的な使い方

### Pointer の parse / format

```ts
import { parsePointer, formatPointer } from "verified-json-reference-parser";

const parsed = parsePointer("/a/b~1c");
if (parsed.ok) {
  console.log(parsed.value); // ["a", "b/c"]
  console.log(formatPointer(parsed.value)); // "/a/b~1c"
}
```

### Pointer を評価する

```ts
import { parsePointer, get } from "verified-json-reference-parser";

const doc = {
  defs: {
    user: { name: "Ada" },
  },
};

const ptr = parsePointer("/defs/user/name");
if (ptr.ok) {
  const result = get(doc, ptr.value);
  console.log(result); // { ok: true, value: "Ada" }
}
```

### ローカル参照を解決する

```ts
import { resolveLocalRef } from "verified-json-reference-parser";

const doc = {
  defs: {
    user: { name: "Ada" },
  },
};

console.log(resolveLocalRef(doc, "#"));
console.log(resolveLocalRef(doc, "#/defs/user"));
```

---

## 4. 意味論モデル

### JSON Pointer

ライブラリは RFC 6901 の Phase 1 振る舞いに従います。

* `""` はドキュメント全体を意味する
* 空でない pointer は `/` で始まらなければならない
* `~0` は `~` に戻る
* `~1` は `/` に戻る
* それ以外の `~` エスケープは `InvalidPointer`

### Pointer 評価

評価は左から右へ進みます。

object に対しては:

* token は完全一致のキーでプロパティを選ぶ
* キーが存在しなければ `NotFound`

array に対しては:

* token は正規形の非負 10 進インデックスでなければならない
* `"0"` は有効
* `"01"`, `"-1"`, `"1.0"` は array index として無効
* 無効な array index token は `TypeMismatch`
* 範囲外インデックスは `NotFound`

primitive に対しては:

* それ以上の走査は `TypeMismatch`

### ローカル参照

対応する形式:

* `#`
* `#/...`

それ以外は Phase 1 の対象外であり、`InvalidPointer` を返します。

---

## 5. エラーハンドリング指針

失敗種別は `kind` で判別します。

* `InvalidPointer`: pointer や local ref の構文が不正
* `TypeMismatch`: 現在の JSON 値の形に対して走査が不正
* `NotFound`: パス自体は妥当だが、対象メンバが存在しない

例:

```ts
import { parsePointer, get } from "verified-json-reference-parser";

const doc = { items: ["a"] };
const p = parsePointer("/items/01");

if (p.ok) {
  const r = get(doc, p.value);
  // { ok: false, kind: "TypeMismatch" }
}
```

`"01"` は pointer 構文エラーとしては扱われません。array に適用された時点で
`TypeMismatch` になります。

---

## 6. 実運用での組み込み方

このライブラリは semantic core であり、完全な resolver ではありません。

JSON Schema エンジン内では、典型的には次のように使います。

1. local `$ref` を parse もしくは受け取る
2. Phase 1 対応形式に対して `resolveLocalRef` を呼ぶ
3. 明示的な `Result` を上位層へ伝搬させる
4. スキーマ読み込みや URI 解決は別レイヤで扱う

推奨事項:

* `kind` を制御フローの一部として扱う
* `TypeMismatch` と `NotFound` を同一視しない
* ネットワークや外部文書解決は別層に分離する

---

## 7. 現在の検証状況

ランタイムライブラリ自体は小さいですが、開発時検証は一般的なユーティリティより
強めに行っています。

現在使っているもの:

* unit test
* property-based test
* 純粋な Python 参照モデル
* Phase 1 の具体ケース向け Z3-backed oracle
* TypeScript 実装との差分検証

この verification layer は開発専用であり、ランタイムには不要です。

---

## 8. 制限事項と非目標

このライブラリに次の機能は期待しないでください。

* リモート文書取得
* 非ローカル参照解決
* RFC 3986 の完全実装
* JSON Schema 文書全体の検証
* バリデータ風の詳細診断メッセージ

必要であれば、これらはこの semantic core の外側に構築してください。
