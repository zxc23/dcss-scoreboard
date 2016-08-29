.PHONY : all
all: yapf pylint

.PHONY : yapf
yapf:
	@echo 'yapf -i'
	@git ls-files '*.py' | xargs -P4 yapf -i

.PHONY : pylint
pylint:
	pylint scoreboard
