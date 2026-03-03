From Stdlib Require Import String.
Open Scope string_scope.

Module Result.
  Inductive t (A : Type) :=
  | Ok : A -> t A
  | Err : string -> t A.

  Arguments Ok {A} _.
  Arguments Err {A} _.
End Result.