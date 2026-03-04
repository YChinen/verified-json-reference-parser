COQC=rocq c
COQFLAGS=-q -R . VerifiedJsonRef

# 依存順：Types -> Token -> TokenLemmas -> Pointer ...
FILES=Types.v Token.v TokenLemmas.v Pointer.v PointerLemmas.v

DOCFILES=Types.v Token.v TokenLemmas.v Pointer.v PointerLemmas.v

all: $(FILES:.v=.vo)

%.vo: %.v
	$(COQC) $(COQFLAGS) $<

clean:
	rm -f *.vo *.vos *.vok *.glob

latex:
	coqdoc --latex --utf8 --interpolate -R . VerifiedJsonRef $(DOCFILES)