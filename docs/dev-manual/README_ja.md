# 開発者マニュアル

このマニュアルは、リポジトリ構成、Phase 1 の semantic core の検証方法、
意味論契約を壊さずに変更する手順を理解したいコントリビュータ向けです。

Phase 1 の対象範囲:

* JSON Pointer の parse / format
* 決定的な pointer 評価
* `#` および `#/...` のローカル JSON Reference 解決

English version: [README.md](./README.md)

規範的意味論: [../architecture/SEMANTICS_ja.md](../architecture/SEMANTICS_ja.md)

---

## 1. リポジトリ構成

ランタイムのコア実装:

* `src/public/types.ts`
* `src/public/pointer.ts`
* `src/public/reference.ts`
* `src/internal/token.ts`
* `src/internal/arrayIndex.ts`

テスト:

* `tests/unit/*.test.ts`
* `tests/pbt/spec_get.ts`
* `tests/pbt/get.pbt.test.ts`

検証ツール:

* `verification/z3/spec.py`
* `verification/z3/z3_model.py`
* `verification/z3/oracle.py`
* `verification/z3/diff.mjs`
* `verification/z3/find_cases.py`
* `verification/z3/find_counterexample.py`
* `verification/z3/find_counterexample_vocab.py`

設計・意味論 docs:

* `docs/architecture/ARCHITECTURE_ja.md`
* `docs/architecture/SEMANTICS_ja.md`
* `docs/architecture/roadmap_ja.md`

---

## 2. コアの振る舞い契約

意味論ドキュメントを規範として扱ってください。

特に、タスクが明示的に意味論変更を要求していない限り、次の不変条件を維持します。

* internal pointer 表現は `readonly string[]`
* `""` は `[]` に parse される
* 空でない pointer string は `/` で始まる必要がある
* unescape として有効なのは `~0` と `~1` のみ
* `get` は純粋・決定的・左から右の評価
* 走査中の array index token format failure は `TypeMismatch`
* object の欠損キーと array の範囲外アクセスは `NotFound`
* `resolveLocalRef` は Phase 1 では `#` と `#/...` のみ対応

意味論を変える場合:

1. ランタイムコードを更新する
2. テストを更新する
3. 必要なら検証ツールも更新する
4. docs を更新する

---

## 3. ランタイム層の責務

### `src/public/pointer.ts`

担当:

* `parsePointer`
* `formatPointer`
* `get`

重要な期待事項:

* 意味論上の例外を投げない
* 構文エラーと走査エラーを明確に分離する
* 暗黙の coercion を入れない

### `src/public/reference.ts`

担当:

* `resolveLocalRef`

Phase 1 の振る舞い:

* `#` は文書全体を返す
* `#/...` は pointer parse と `get` で解決する
* それ以外は `InvalidPointer`

---

## 4. 検証スタック

このリポジトリは、開発時 assurance を複数層で行っています。

### unit test

境界条件とエッジケースを直接検証します。

### property-based test

`tests/pbt/get.pbt.test.ts` では、`tests/pbt/spec_get.ts` の TypeScript spec
model とランタイム実装を比較します。

### Python 参照モデル

`verification/z3/spec.py` は、Phase 1 意味論のもっとも単純な実行可能 baseline
として残します。小さく読みやすく保ってください。

### Z3-backed oracle

`verification/z3/z3_model.py` は SMT ベースの判定ロジックで具体的な Phase 1 case
を評価し、最終的な `Result<JSONValue>` を再構成します。

`verification/z3/oracle.py` は CLI adapter です。移行期やデバッグ時には次を切り替えて
呼べます。

* Python baseline
* Z3-backed oracle

### 差分検証

`verification/z3/diff.mjs` は `dist/` の TypeScript 実装と oracle を
verification corpus 上で比較します。

### 反例探索

`find_counterexample.py` と `find_counterexample_vocab.py` は、bounded pool と
solver-assisted selection を使って意味論不一致を探索します。

---

## 5. 意味論を安全に変更する手順

推奨ワークフロー:

1. 影響を受けるランタイムファイルと対応テストを読む
2. 意味論ドキュメントを読み直す
3. 契約に合う最小の振る舞い変更を行う
4. テストを更新または追加する
5. observable behavior が変わったら検証ツールや corpus を更新する
6. 必要最小限の検証セットを実行する

pointer semantics を触る場合は、次も必ず確認してください。

* array index classification
* escape / unescape 処理
* `resolveLocalRef` のエッジケース

---

## 6. 検証コマンド

依存関係の導入:

```bash
npm install
python -m pip install -r verification/z3/requirements.txt
```

ビルド:

```bash
npm run build
```

型チェック:

```bash
npm run typecheck
```

テスト:

```bash
npm run test:run
```

差分検証:

```bash
npm run verify:z3
```

Python 側 parity check:

```bash
python verification/z3/check_oracle_parity.py
python verification/z3/test_z3_model.py
```

反例探索:

```bash
python verification/z3/find_counterexample.py
python verification/z3/find_counterexample_vocab.py
```

---

## 7. 検証ツール編集時のルール

`verification/z3/` を編集する際は:

* ランタイム意味論を verification layer に埋め込まない
* Z3 oracle の対象が広がっても、`spec.py` は読みやすい baseline として残す
* corpus の意味を変えたら、生成ケースも更新する
* ロジックを重複させるより、関心ごとごとに共有 source を持つ

補足:

* `diff.mjs` は `src/` ではなく `dist/` を読む
* verifier は開発専用
* 性能も重要だが、意味論の明瞭さを優先する

---

## 8. よくある失敗

次の誤りに注意してください。

* 不正な array index token を `InvalidPointer` にする
* 欠損 object property に `TypeMismatch` を返す
* `NotFound` と `TypeMismatch` を潰してしまう
* docs と tests を更新せずに `resolveLocalRef` の対応範囲を広げる
* ランタイム意味論を変えたのに verification corpus を更新しない

---

## 9. コントリビューション前チェックリスト

意味論または検証まわりの作業を終える前に確認すること:

* public API は意図的に小さいままか
* Result shape は意図せず変わっていないか
* ランタイムコードは純粋かつ決定的か
* 変更境界をテストがカバーしているか
* verification script がランタイム契約と一致しているか
* docs を更新したなら英語版と日本語版が揃っているか
