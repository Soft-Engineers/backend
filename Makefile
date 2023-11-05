all:
	@echo "Building..."

	@echo "Building complete."

.PHONY: clean

clean:
	@echo "Cleaning up..."
	@rm -f Database/lacosa.sqlite
	@echo "Cleanup complete."
