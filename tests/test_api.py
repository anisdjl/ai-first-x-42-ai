import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.audit import UserRole
import os

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

@pytest.mark.asyncio
async def test_ui_served():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Atelier Nova" in response.text



@pytest.mark.asyncio
async def test_job_posting_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/job-posting")
    assert response.status_code == 200
    data = response.json()
    assert "Développeur" in data["titre"]
    assert len(data["criteres_explicites"]) >= 5

@pytest.mark.asyncio
async def test_product_decisions():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/product-decisions")
    assert response.status_code == 200
    data = response.json()
    assert "decision_1_conservation_fichier" in data
    assert "decision_2_vue_manager" in data
    assert "decision_3_duree_conservation" in data

@pytest.mark.asyncio
async def test_upload_and_pipeline_with_example_cv():
    transport = ASGITransport(app=app)
    # On utilise cv-exemple-agent.md pour le test
    example_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cv-exemple-agent.md")
    assert os.path.exists(example_path)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with open(example_path, "rb") as f:
            files = {"file": ("cv-exemple-agent.md", f, "text/markdown")}
            response = await ac.post("/api/v1/candidates/upload?user_role=recruteur", files=files)
        
        assert response.status_code == 200
        res_data = response.json()
        cand = res_data["candidate"]
        cand_id = cand["id"]
        assert cand_id is not None
        assert cand["anonymous_id"].startswith("CANDIDAT-")

        # Vérification minimisation : aucune donnée de naissance / marital
        extracted = cand["extracted_data"]
        assert "experiences" in extracted
        assert "competences" in extracted

        # Test RBAC Manager : ne doit PAS voir les coordonnées directes
        resp_manager = await ac.get(f"/api/v1/candidates/{cand_id}?user_role=manager")
        assert resp_manager.status_code == 200
        assert resp_manager.json()["contact"] is None

        # Test RBAC Manager : tentative d'accès coordonnées -> 403 Forbidden
        resp_forbidden_contact = await ac.get(f"/api/v1/candidates/{cand_id}/contact?user_role=manager")
        assert resp_forbidden_contact.status_code == 403

        # Test RBAC Manager : tentative de suppression -> 403 Forbidden
        resp_forbidden_delete = await ac.delete(f"/api/v1/candidates/{cand_id}?user_role=manager")
        assert resp_forbidden_delete.status_code == 403

        # Test Réciprocité Recruteur : accès coordonnées OK
        resp_recruteur_contact = await ac.get(f"/api/v1/candidates/{cand_id}/contact?user_role=recruteur")
        assert resp_recruteur_contact.status_code == 200
        assert resp_recruteur_contact.json()["email"] is not None

        # Test Transparence : inspection du prompt
        resp_prompt = await ac.get(f"/api/v1/candidates/{cand_id}/prompt-context")
        assert resp_prompt.status_code == 200
        assert "prompt_extraction" in resp_prompt.json()

        # Test Mention d'information RGPD
        resp_notice = await ac.get(f"/api/v1/candidates/{cand_id}/notice")
        assert resp_notice.status_code == 200
        assert "Atelier Nova" in resp_notice.json()["notice_text"]

        # Test Portabilité (Export)
        resp_export = await ac.get(f"/api/v1/candidates/{cand_id}/export")
        assert resp_export.status_code == 200
        assert resp_export.json()["identifiant_systeme"] == cand_id

        # Test Droit à l'oubli : suppression par le recruteur
        resp_del = await ac.delete(f"/api/v1/candidates/{cand_id}?user_role=recruteur")
        assert resp_del.status_code == 200

        # Vérification qu'il n'existe plus en base
        resp_check = await ac.get(f"/api/v1/candidates/{cand_id}")
        assert resp_check.status_code == 404

        # Vérification journal d'audit
        resp_logs = await ac.get("/api/v1/audit/logs")
        assert resp_logs.status_code == 200
        logs = resp_logs.json()
        actions = [l["action"] for l in logs]
        assert "import" in actions
        assert "effacement" in actions
