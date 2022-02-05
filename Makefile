up_local_compose:
	docker-compose -f docker-compose-ci-test.yaml -f docker-compose-local.yaml up -d

down_local_compose:
	docker-compose -f docker-compose-ci-test.yaml -f docker-compose-local.yaml down

run_tests:
	docker-compose -f docker-compose-ci-test.yaml up

linters:
	black . && isort .