# End-to-end project run. Targets are thin wrappers over `uv run modal ...`.
#
# 3 tasks × 4 variants × 5 seeds = 60 SAC runs on Modal with 10x H100 concurrency.

VOLUME    := cs285-data
LOCAL_OUT := output
UV        := uv run

.PHONY: all sync smoke sweep fetch analysis clean

all: sweep fetch analysis

sync:
	uv sync

smoke:
	$(UV) modal run modal_app.py::smoke

# --detach keeps the remote app alive even if the local client disconnects.
# Without it, a laptop sleep or network blip stops every running container.
sweep:
	$(UV) modal run --detach modal_app.py::sweep

fetch:
	$(UV) modal volume get --force $(VOLUME) /runs $(LOCAL_OUT)

analysis:
	$(UV) python analyze.py

clean:
	rm -rf $(LOCAL_OUT)
