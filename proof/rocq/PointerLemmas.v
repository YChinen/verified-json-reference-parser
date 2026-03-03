From Stdlib Require Import String Ascii List.
From VerifiedJsonRef Require Import Types Token TokenLemmas Pointer.
Import Types.
Import ListNotations.
Open Scope string_scope.

Lemma append_empty_r : forall s : string, s ++ EmptyString = s.
Proof.
  intro s.
  induction s as [|c rest IH]; simpl.
  - reflexivity.
  - now rewrite IH.
Qed.

Lemma append_empty_l : forall s : string, EmptyString ++ s = s.
Proof. intro s; reflexivity. Qed.

Lemma append_assoc : forall a b c : string, (a ++ b) ++ c = a ++ (b ++ c).
Proof.
  intro a; induction a as [|x a IH]; intros b c; simpl.
  - reflexivity.
  - now rewrite IH.
Qed.

Lemma cons_empty_append : forall (c : ascii) (s : string),
  (String c EmptyString) ++ s = String c s.
Proof.
  intros c s. simpl. reflexivity.
Qed.

Module PointerLemmas.
  Import Token.
  Import Pointer.
  Import TokenLemmas.

  (* --- 既にOK：mapM_unescape (map escapeToken p) = Ok p --- *)
  Lemma mapM_unescape_escape_ok :
    forall p, mapM_unescape (map escapeToken p) = Ok p.
  Proof.
    induction p as [|t rest IH]; simpl.
    - reflexivity.
    - rewrite unescape_escape_roundtrip.
      simpl.
      now rewrite IH.
  Qed.

  (* scan_segments の基底 *)
  Lemma scan_segments_empty :
    forall cur, scan_segments EmptyString cur = [cur].
  Proof. intro cur; simpl; reflexivity. Qed.

  (* NoSlash: 文字列に "/" が出ない *)
  Inductive NoSlash : string -> Prop :=
  | NS_Empty : NoSlash EmptyString
  | NS_Cons  : forall c rest,
      c <> "/"%char ->
      NoSlash rest ->
      NoSlash (String c rest).

  (* escapeToken の結果には "/" が出ない *)
  Lemma noslash_escapeToken :
    forall s, NoSlash (escapeToken s).
  Proof.
    induction s as [|c rest IH]; simpl.
    - constructor.
    - destruct (ascii_dec c "~"%char) as [Htilde|Htilde].
      + (* "~" -> "~0" *)
        constructor.
        * discriminate.
        * constructor.
          { discriminate. }
          exact IH.
      + destruct (ascii_dec c "/"%char) as [Hslash|Hslash].
        * (* "/" -> "~1" *)
          constructor.
          { discriminate. }
          constructor.
          { discriminate. }
          exact IH.
        * (* other char *)
          constructor.
          { (* c <> "/" *)
            intro H; apply Hslash; exact H.
          }
          exact IH.
  Qed.

  (* NoSlash s なら scan_segments (s ++ rest) cur は s を丸ごと cur に吸収できる *)
  Lemma scan_segments_append_noslash :
    forall s rest cur,
      NoSlash s ->
      scan_segments (s ++ rest) cur = scan_segments rest (cur ++ s).
  Proof.
    induction s as [|c s' IH]; intros rest cur Hns; simpl in *.
    - (* s = "" *)
      rewrite append_empty_r.
      reflexivity.
    - inversion Hns as [|c0 rest0 Hneq Hns']; subst.
      (* (String c s') ++ rest = String c (s' ++ rest) *)
      simpl.
      destruct (ascii_dec c "/"%char) as [Hslash|Hslash].
      + exfalso; apply Hneq; exact Hslash.
      + (* not slash *)
        specialize (IH rest (cur ++ String c EmptyString) Hns').

        (* IH の右辺にある ((cur ++ "c") ++ s') を cur ++ ("c" ++ s') にする *)
        rewrite (append_assoc cur (String c EmptyString) s') in IH.

        (* ("c" ++ s') を String c s' に潰す *)
        rewrite (cons_empty_append c s') in IH.

        exact IH.
  Qed.

  (* formatTail と scan_segments が噛み合う：任意curで「cur :: map escapeToken ts」になる *)
  Lemma scan_segments_formatTail_cur :
    forall ts cur,
      scan_segments (formatTail ts) cur = cur :: map escapeToken ts.
  Proof.
    induction ts as [|t rest IH]; intros cur; simpl.
    - (* ts = [] *)
      reflexivity.
    - (* ts = t :: rest *)
      (* formatTail (t::rest) = "/" ++ escapeToken t ++ formatTail rest *)
      (* "/" ++ x は String "/" x に簡約される *)
      simpl.
      (* scan_segments は先頭 "/" を見て cur を切る *)
      destruct (ascii_dec "/"%char "/"%char) as [_|H]; [|contradiction].
      simpl.
      (* ここで scan_segments (escapeToken t ++ formatTail rest) "" を扱う *)
      rewrite (scan_segments_append_noslash (escapeToken t) (formatTail rest) EmptyString).
      2:{ apply noslash_escapeToken. }
      (* 右側は scan_segments (formatTail rest) ("" ++ escapeToken t) *)
      simpl.
      (* IH 適用 *)
      specialize (IH (escapeToken t)).
      rewrite IH.
      reflexivity.
  Qed.

  (* drop1(formatPointer (t::ts)) を scan すると map escapeToken (t::ts) になる *)
  Lemma scan_segments_drop1_formatPointer_nonempty :
    forall t ts,
      scan_segments (drop1 (formatPointer (t :: ts))) EmptyString
      = map escapeToken (t :: ts).
  Proof.
    intros t ts.
    unfold formatPointer.
    simpl.
    (* drop1 ("/" ++ ...) = ... *)
    (* (String "/" EmptyString) ++ x は String "/" x に簡約 *)
    (* よって drop1 (String "/" something) = something *)
    simpl.
    (* 残りは escapeToken t ++ formatTail ts *)
    rewrite (scan_segments_append_noslash (escapeToken t) (formatTail ts) EmptyString).
    2:{ apply noslash_escapeToken. }
    simpl.
    (* scan_segments (formatTail ts) (escapeToken t) = escapeToken t :: map escapeToken ts *)
    rewrite (scan_segments_formatTail_cur ts (escapeToken t)).
    reflexivity.
  Qed.

  (* 最終：parsePointer(formatPointer p) = Ok p *)
  Theorem parse_format_roundtrip :
    forall p, parsePointer (formatPointer p) = Ok p.
  Proof.
    intro p.
    destruct p as [|t ts].
    - (* p = [] *)
      simpl.
      (* parsePointer "" = Ok [] *)
      unfold parsePointer.
      simpl.
      destruct (string_dec EmptyString EmptyString); reflexivity.
    - (* p = t :: ts *)
    (* ps を固定 *)
    set (ps := formatPointer (t :: ts)).

    unfold parsePointer.
    (* parsePointer ps の形にする *)
    fold ps.

    (* まず ps <> "" を示して string_dec 分岐を潰す *)
    destruct (string_dec ps EmptyString) as [Heq|Hneq].
    + (* ps = "" は矛盾 *)
        subst ps.
        unfold formatPointer in Heq.
        simpl in Heq.
        discriminate.
    + (* starts_with_slash ps = true を示して分岐を潰す *)
        destruct (starts_with_slash ps) eqn:Hsw.
        * (* true 分岐：ここで goal 内に scan_segments (drop1 ps) "" が現れる *)
        (* ここで ps を元に戻す（rewrite 用） *)
        subst ps.

        (* ここで初めて scan_segments_drop1_formatPointer_nonempty が当たる形になる *)
        rewrite scan_segments_drop1_formatPointer_nonempty.

        (* mapM_unescape (map escapeToken (t::ts)) = Ok (t::ts) *)
        exact (mapM_unescape_escape_ok (t :: ts)).
        * (* false は矛盾：formatPointer は必ず "/" で始まる *)
        subst ps.
        unfold starts_with_slash in Hsw.
        unfold formatPointer in Hsw; simpl in Hsw.
        destruct (ascii_dec "/"%char "/"%char); try discriminate.
  Qed.

End PointerLemmas.