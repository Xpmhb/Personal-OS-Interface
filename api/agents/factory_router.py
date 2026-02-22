from fastapi import APIRouter, HTTPException
from agents.schemas import FactoryStartRequest, FactoryClarifyRequest
from agents.factory import start_creation, process_answers

router = APIRouter()


@router.post("/start")
async def factory_start(request: FactoryStartRequest):
    """Start agent creation from natural language"""
    result = await start_creation(request.description)
    return result


@router.post("/clarify")
async def factory_clarify(request: FactoryClarifyRequest):
    """Submit answers to clarifying questions and generate spec"""
    try:
        result = await process_answers(request.session_id, request.answers)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/generate")
async def factory_generate(request: FactoryClarifyRequest):
    """Alias for /clarify — generates final spec from answers"""
    try:
        result = await process_answers(request.session_id, request.answers)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
