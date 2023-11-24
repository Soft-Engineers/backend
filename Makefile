.PHONY: clean start clean-start test full-test

start: 
	uvicorn app:app --reload

start-exposed: 
	uvicorn app:app --reload --host 0.0.0.0

clean:
	@echo "Cleaning up..."
	@rm -f Database/lacosa.sqlite
	@echo "Cleanup complete."

clean-start: clean start

test:
	coverage run -m --source=. pytest Tests 

full-test: test
	coverage report

