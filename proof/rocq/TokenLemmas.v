From Stdlib Require Import String Ascii.
From VerifiedJsonRef Require Import Types Token.
Import Types.
Open Scope string_scope.

Module TokenLemmas.
  Import Token.

  Theorem unescape_escape_roundtrip :
    forall s, unescapeToken (escapeToken s) = Ok s.
  Proof.
    induction s as [|c rest IH]; simpl.
    - reflexivity.
    - destruct (ascii_dec c "~"%char) as [Htilde|Htilde]; simpl.
      + subst c.
        (* "~" -> "~0" *)
        destruct (ascii_dec "~"%char "~"%char) as [_|H]; [|contradiction].
        simpl.
        destruct (ascii_dec "0"%char "0"%char) as [_|H0]; [|contradiction].
        simpl.
        now rewrite IH.
      + destruct (ascii_dec c "/"%char) as [Hslash|Hslash]; simpl.
        * subst c.
          (* "/" -> "~1" *)
          destruct (ascii_dec "/"%char "~"%char) as [H|_].
          { discriminate. }
          simpl.
          destruct (ascii_dec "~"%char "~"%char) as [_|H]; [|contradiction].
          simpl.
          destruct (ascii_dec "1"%char "0"%char) as [H10|_].
          { discriminate. }
          simpl.
          destruct (ascii_dec "1"%char "1"%char) as [_|H11]; [|contradiction].
          simpl.
          now rewrite IH.
        * (* その他の文字 *)
          destruct (ascii_dec c "~"%char) as [H|_].
          { contradiction. }
          simpl.
          now rewrite IH.
  Qed.

End TokenLemmas.