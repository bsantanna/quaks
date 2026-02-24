cleanup:
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
	python -m flake8 .
