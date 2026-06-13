.PHONY: test lint release

test:
	pytest

lint:
	ruff check . && ruff format --check .

release:
	@test -n "$(v)" || (echo "usage: make release v=0.2.0" && exit 1)
	@grep -q "$(v)" CHANGELOG.md || (echo "add $(v) entry to CHANGELOG.md first" && exit 1)
	sed -i 's/^version = .*/version = "$(v)"/' pyproject.toml
	git add pyproject.toml CHANGELOG.md
	git commit -m "chore: release v$(v)"
	git tag v$(v)
	git push origin main --tags
	@echo "released v$(v)"
