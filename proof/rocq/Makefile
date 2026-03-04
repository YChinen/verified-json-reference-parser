COQC=rocq c
COQFLAGS=-q -R . VerifiedJsonRef

# 依存順：Types -> Token -> TokenLemmas -> Pointer ...
FILES=Types.v Token.v TokenLemmas.v Pointer.v PointerLemmas.v

DOCFILES=Types.v Token.v TokenLemmas.v Pointer.v PointerLemmas.v

all: $(FILES:.v=.vo)
	 
%.vo: %.v
	$(COQC) $(COQFLAGS) $<

latex:
	rocq doc -o proof.tex --latex --interpolate -R . VerifiedJsonRef $(DOCFILES)
	mkdir docs
	pdflatex --output-directory=./docs -interaction=nonstopmode -file-line-error -synctex=1 proof.tex

clean:
	rm -rf docs/
	rm -f *.vo *.vos *.vok *.glob *.aux *.log *.tex *.pdf *.toc *.out *.aux *.nav *.snm *.sty .*.aux