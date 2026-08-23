.PHONY: run test clean docker

run:
	./scripts/run_pipeline.sh

test:
	./scripts/run_tests.sh

docker:
	docker compose run --rm etl

clean:
	rm -f warehouse/retail_analytics.db
	rm -rf data/rejected

