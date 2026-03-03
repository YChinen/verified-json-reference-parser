From Stdlib Require Import String Ascii List.
From VerifiedJsonRef Require Import Types Token.
Import Types.
Import ListNotations.
Open Scope string_scope.

Module Pointer.

  Definition Pointer := list string.

  Definition starts_with_slash (s : string) : bool :=
    match s with
    | EmptyString => false
    | String c _ => if ascii_dec c "/"%char then true else false
    end.

  Definition drop1 (s : string) : string :=
    match s with
    | EmptyString => EmptyString
    | String _ rest => rest
    end.

  (* セグメントを走査して分割（空セグメントも保持） *)
  Fixpoint scan_segments (s : string) (cur : string) : list string :=
    match s with
    | EmptyString => [cur]
    | String c rest =>
        if ascii_dec c "/"%char then
          cur :: scan_segments rest EmptyString
        else
          scan_segments rest (cur ++ String c EmptyString)
    end.

  Fixpoint mapM_unescape (segs : list string) : Result (list string) :=
    match segs with
    | [] => Ok []
    | seg :: rest =>
        match Token.unescapeToken seg with
        | Err e => Err e
        | Ok t =>
            match mapM_unescape rest with
            | Err e => Err e
            | Ok ts => Ok (t :: ts)
            end
        end
    end.

  Definition parsePointer (ps : string) : Result Pointer :=
    if string_dec ps EmptyString then Ok []
    else if starts_with_slash ps then
      mapM_unescape (scan_segments (drop1 ps) EmptyString)
    else Err InvalidPointer.

  Fixpoint formatTail (p : Pointer) : string :=
    match p with
    | [] => EmptyString
    | t :: ts =>
        (String "/"%char EmptyString) ++ (Token.escapeToken t) ++ (formatTail ts)
    end.

  Definition formatPointer (p : Pointer) : string :=
    match p with
    | [] => EmptyString
    | t :: ts =>
        (String "/"%char EmptyString) ++ (Token.escapeToken t) ++ (formatTail ts)
    end.

End Pointer.