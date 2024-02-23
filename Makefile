
all: test docs

docs:
	black piecad/*.py tests/*.py doc_examples/*.example
	rm -rf html/piecad
	pdoc3 --html piecad --force
	(cd doc_examples; ./mk_doc_examples)

test:
	pytest tests --benchmark-disable

benchmark:
	pytest tests --benchmark-only

savebenchmark:
	(read -p "Benchmark Name: " -r NAME ; pytest tests --benchmark-only --benchmark-save=`date +%F`"$${NAME}" --benchmark-name=short)
