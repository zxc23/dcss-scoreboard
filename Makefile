.PHONY : all
all: yapf pylint mypy

.PHONY : yapf
yapf:
	@echo 'yapf -i'
	@git ls-files '*.py' | xargs -P4 -n1 yapf -i

.PHONY : pylint
pylint:
	pylint scoreboard

.PHONY : mypy
mypy:
	@echo 'mypy'
	@git ls-files '*.py' | xargs -P4 -n1 mypy --silent-imports --strict-optional --warn-unused-ignores --warn-redundant-casts --check-untyped-defs --disallow-untyped-defs
