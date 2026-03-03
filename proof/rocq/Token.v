From Stdlib Require Import String Ascii.
From VerifiedJsonRef Require Import Types.
Import Types.
Open Scope string_scope.

Module Token.

  Fixpoint escapeToken (s : string) : string :=
    match s with
    | EmptyString => EmptyString
    | String c rest =>
        if ascii_dec c "~"%char then
          String "~"%char (String "0"%char (escapeToken rest))
        else if ascii_dec c "/"%char then
          String "~"%char (String "1"%char (escapeToken rest))
        else
          String c (escapeToken rest)
    end.

  Fixpoint unescapeToken (s : string) : Result string :=
    match s with
    | EmptyString => Ok EmptyString
    | String c rest =>
        if ascii_dec c "~"%char then
          match rest with
          | EmptyString => Err InvalidPointer
          | String d rest' =>
              if ascii_dec d "0"%char then
                match unescapeToken rest' with
                | Ok out => Ok (String "~"%char out)
                | Err e => Err e
                end
              else if ascii_dec d "1"%char then
                match unescapeToken rest' with
                | Ok out => Ok (String "/"%char out)
                | Err e => Err e
                end
              else Err InvalidPointer
          end
        else
          match unescapeToken rest with
          | Ok out => Ok (String c out)
          | Err e => Err e
          end
    end.

End Token.