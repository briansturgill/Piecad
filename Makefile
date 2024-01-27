
all: test
	black src/*.py tests/*.py
	pdoc3 --html piecad --force
	(cd doc_examples; ./mk_doc_examples)

test:
	pytest tests --benchmark-disable

benchmark:
	pytest tests --benchmark-only

savebenchmark:
	pytest tests --benchmark-only --benchmark-save=`date +%F` --benchmark-name=short
