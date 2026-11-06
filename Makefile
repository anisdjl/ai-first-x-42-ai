.PHONY: help install start run test clean mongo-start ollama-check

help:
	@echo "=========================================================="
	@echo "  Atelier Nova - Assistant RH Local (Souverain & RGPD)    "
	@echo "=========================================================="
	@echo "Commandes disponibles :"
	@echo "  make install      - Installe les dépendances avec uv"
	@echo "  make run          - Démarre MongoDB et lance le backend FastAPI"
	@echo "  make test         - Exécute les tests unitaires et RGPD"
	@echo "  make mongo-start  - Démarre le service MongoDB local"
	@echo "  make ollama-check - Vérifie si Ollama et le modèle sont prêts"
	@echo "  make clean        - Nettoie les caches (__pycache__, pytest)"
	@echo "=========================================================="

install:
	uv sync

mongo-start:
	brew services start mongodb/brew/mongodb-community || true

ollama-check:
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama est en cours d'exécution" || (echo "❌ Ollama n'est pas lancé. Lancez : ollama serve &" && exit 1)
	@ollama list | grep -q "ministral-3:3b" && echo "✅ Modèle ministral-3:3b prêt" || echo "⚠️ Modèle ministral-3:3b manquant. Exécutez : ollama pull ministral-3:3b"

run: mongo-start
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	uv run pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
