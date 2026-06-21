from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.openrouter import list_models, chat

router = APIRouter()

class ValidateKeyRequest(BaseModel):
    key: str

@router.post("/validate-key")
async def validate_key(payload: ValidateKeyRequest):
    try:
        models = await list_models(payload.key)
        return {"valid": True, "model_count": len(models)}
    except Exception as e:
        raise HTTPException(400, f"Invalid key: {str(e)}")

@router.get("/models")
async def get_models(key: str):
    try:
        models = await list_models(key)
        return {"models": [{"id": m["id"], "name": m.get("name", m["id"])} for m in models]}
    except Exception as e:
        raise HTTPException(400, str(e))
