import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.config import SettingsAPI
from models import CompanyReportRequest, StructuredBusinessAnalysis
from agents import CompanyIntelligenceAgent, OpenAIConnector
from DB.ReportStore import ReportStore

# Load .env
load_dotenv()

# ─── LLM connectors ─────────────────────────────────────────────────────────
_model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
_fast_model  = os.getenv("LLM_FAST_MODEL", "gpt-4o-mini")

llm_connector      = OpenAIConnector(model=_model_name, temperature=0.0, max_tokens=4000)
fast_llm_connector = OpenAIConnector(model=_fast_model,  temperature=0.0, max_tokens=512)

# ─── Agent (compiled once at startup) ───────────────────────────────────────
agent = CompanyIntelligenceAgent(
    llm_connector=llm_connector,
    fast_llm_connector=fast_llm_connector,
)

# ─── Report store (Qdrant-backed) ────────────────────────────────────────────
report_store = ReportStore(host="qdrant", port=6333)

# ─── FastAPI application ─────────────────────────────────────────────────────
app = FastAPI(title="Company Intelligence API")
SettingsAPI(app, corsFlag=True)


@app.on_event("startup")
async def startup_event():
    print(f"Company Intelligence Agent started (model={_model_name}).")


@app.get("/start")
async def root():
    return {"message": "Company Intelligence Agent backend is running."}


# ─── Generate & persist ──────────────────────────────────────────────────────

@app.post("/api/generate-report", response_model=StructuredBusinessAnalysis)
async def generate_report(request: CompanyReportRequest):
    """
    Run the LangGraph pipeline, persist the result to Qdrant, and return it.
    """
    print(f"[REQUEST] company='{request.company_name}'  region='{request.company_region}'")
    try:
        report = await agent.generate_report(
            company_name=request.company_name,
            company_region=request.company_region,
        )

        # Persist to Qdrant (fire-and-forget — don't let storage failures block the response)
        try:
            report_dict = report.model_dump()
            report_id = report_store.save(
                company_name=request.company_name,
                company_region=request.company_region,
                report=report_dict,
            )
            print(f"[SAVED] report_id={report_id}")
        except Exception as store_err:
            print(f"[WARN] Failed to save report to Qdrant: {store_err}")

        return report.model_dump()

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─── History endpoints ────────────────────────────────────────────────────────

@app.get("/api/reports")
async def list_reports():
    """
    Return a list of all previously generated report summaries (for the sidebar).
    Each item: { id, company_name, company_region, created_at }
    """
    try:
        return report_store.list_all(limit=100)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """
    Fetch the full report payload for a previously saved report by its UUID.
    """
    try:
        report = report_store.get_by_id(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found.")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/reports/{report_id}", status_code=204)
async def delete_report(report_id: str):
    """
    Delete a previously saved report from Qdrant by its UUID.
    Returns 204 No Content on success, 404 if not found.
    """
    try:
        deleted = report_store.delete(report_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Report not found.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
