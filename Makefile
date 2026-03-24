github cleanup:
	rm agent_lab.db || true
	rm temp* || true

reset:
	docker compose stop
	docker compose rm -f

run:
	docker compose up --build -d

test:
	pytest --cov=app --cov-report=xml; bash -c 'cd frontend && npm test';  $(MAKE) cleanup

lint:
	# stop the build if there are Python syntax errors or undefined names
	python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings
	python -m flake8 . --count --exit-zero --statistics
