From Stdlib Require Import String.
Open Scope string_scope.

Module Types.
  Inductive ErrorKind :=
  | InvalidPointer
  | TypeMismatch
  | NotFound.

  Inductive Result (A : Type) :=
  | Ok : A -> Result A
  | Err : ErrorKind -> Result A.

  Arguments Ok {A} _.
  Arguments Err {A} _.
End Types.