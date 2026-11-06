.PHONY: help install start run test clean mongo-start ollama-check certs nginx-start nginx-stop nginx-reload

help:
	@echo "=========================================================="
	@echo "  Atelier Nova - Assistant RH Local (Souverain & RGPD)    "
	@echo "=========================================================="
	@echo "Commandes disponibles :"
	@echo "  make install      - Installe les dépendances avec uv"
	@echo "  make run          - Démarre MongoDB et lance le backend FastAPI (port 8000)"
	@echo "  make certs        - Génère le certificat TLS auto-signé pour HTTPS"
	@echo "  make nginx-start  - Lance le proxy Nginx TLS sécurisé (https://localhost:8443)"
	@echo "  make nginx-stop   - Arrête le proxy Nginx"
	@echo "  make test         - Exécute les tests unitaires et RGPD"
	@echo "  make mongo-start  - Démarre le service MongoDB local"
	@echo "  make ollama-check - Vérifie si Ollama et le modèle sont prêts"
	@echo "  make clean        - Nettoie les caches (__pycache__, pytest)"
	@echo "=========================================================="

install:
	uv sync

certs:
	@mkdir -p certs
	@test -f certs/cert.pem || openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -subj "/C=FR/ST=Loire-Atlantique/L=Nantes/O=Atelier Nova/CN=localhost"
	@echo "✅ Certificats TLS prêts dans certs/"

nginx-start: certs
	@mkdir -p /tmp/nginx_client_temp /tmp/nginx_proxy_temp /tmp/nginx_fastcgi_temp /tmp/nginx_uwsgi_temp /tmp/nginx_scgi_temp
	@nginx -p . -c $(PWD)/nginx.conf && echo "✅ Nginx TLS actif : https://localhost:8443 (HTTP: http://localhost:8080)" || echo "Nginx est déjà lancé ou en erreur"

nginx-stop:
	@test -f /tmp/nginx_atelier_nova.pid && nginx -p . -c $(PWD)/nginx.conf -s stop && rm -f /tmp/nginx_atelier_nova.pid && echo "✅ Nginx arrêté" || echo "Nginx n'est pas actif"

nginx-reload:
	@nginx -p . -c $(PWD)/nginx.conf -s reload && echo "✅ Configuration Nginx rechargée"

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

