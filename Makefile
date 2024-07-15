# Test Project
test:: 
	pytest tests

format::
	toml-sort pyproject.toml

# Build the project
build:: format test
	poetry lock
	toml-sort pyproject.toml
	poetry build

# Publish the project
publish:: build
	poetry publish