
all: test docs

docs:
	black piecad/*.py tests/*.py doc_examples/*.example examples/*.py
	rm -rf docs/*
	pdoc3 --html piecad --force
	(cd doc_examples; ./mk_doc_examples)
	mv html/piecad docs
	rmdir html

test:
	pytest tests --benchmark-disable

benchmark:
	pytest tests --benchmark-only

savebenchmark:
	(read -p "Benchmark Name: " -r NAME ; pytest tests --benchmark-only --benchmark-save=`date +%F`"$${NAME}" --benchmark-name=short)

clean:
	rm -f examples/*.obj
