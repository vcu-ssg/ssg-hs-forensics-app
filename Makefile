# =========================================================
# Cross-platform Environment Detection
# =========================================================
ifeq ($(OS),Windows_NT)
    IS_WINDOWS := 1
    SHELL := pwsh.exe -NoProfile -NoLogo -ExecutionPolicy Bypass
    OPEN := powershell.exe -NoProfile -Command "Start-Process"
else
    IS_WINDOWS := 0
    SHELL := /bin/bash
    OPEN := xdg-open
endif

# =========================================================
# Target Descriptions
# =========================================================
help.title                  = Show this help message
forensics-ui.title          = Build the frontend using Quarto
forensics-backend.title     = Build the backend without running server
start-server.title          = Start backend in detached mode (listens on localhost:80)
stop-server.title           = Stop backend server
open-webapp.title           = Start server (if needed) and open the browser

# =========================================================
# PHONY Targets
# =========================================================
.PHONY: help forensics-ui forensics-backend start-server stop-server open-webapp

# =========================================================
# Auto-help target that prints all *.title descriptions
# =========================================================
help:
	@echo "Available commands:"
	@echo "-------------------"
	@grep -E '^[a-zA-Z0-9_.-]+\.title' $(MAKEFILE_LIST) | \
	  sed -E 's/^(.*)\.title[ ]*=[ ]*(.*)/\1\t\2/' 

# =========================================================
# Targets
# =========================================================

forensics-ui:
	cd forensics-ui && quarto render

forensics-backend:
	cd forensics-backend && docker compose build

start-server:
	cd forensics-backend && docker compose up --build --detach

stop-server:
	cd forensics-backend && docker compose down

open-webapp: start-server
	$(OPEN) "http://localhost"
