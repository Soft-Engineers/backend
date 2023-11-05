.PHONY: clean start clean-start

start: 
	uvicorn app:app --reload

clean:
	@echo "Cleaning up..."
	@rm -f Database/lacosa.sqlite
	@echo "Cleanup complete."

clean-start: clean start

