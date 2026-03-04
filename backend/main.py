from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.config import SettingsAPI
import asyncio

# Our models and application logic
from models import CompanyReportRequest, StructuredBusinessAnalysis
from LLM import LLM
from search_agent import SearchAgent
from scraper import WebScraper

import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# LLM Settings
local_api_base = os.getenv("LLM_API_BASE", None) # Defaults to None, meaning official OpenAI
local_api_key = os.getenv("OPENAI_KEY", "your-openai-key")
model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o") # Use gpt-4o-mini for fast, inexpensive structured output

app = FastAPI()


# Initialize Settings, CORS
SettingsAPI(app, corsFlag=True)

@app.on_event("startup")
async def startup_event():
    print("Application started.")

@app.get("/start")
async def root():
    return {"message": "Hello World. Agent Backend Running."}

@app.post("/api/generate-report", response_model=StructuredBusinessAnalysis)
async def generate_report(request: CompanyReportRequest):
    try:
        print(f"Received request to analyze '{request.company_name}' in '{request.company_region}'")

        # 1. Search for info using DDGS
        search_agent = SearchAgent()
        print("Searching DuckDuckGo...")
        initial_results = search_agent.search_company_info(
            company_name=request.company_name, 
            country=request.company_region,
            max_results=4
        )
        
        # 2. Scrape underlying URLs to get more text
        scraper = WebScraper(timeout=15)
        print(f"Scraping URLs ({len(initial_results)} links found)...")
        enriched_results = await scraper.scrape_urls(initial_results)
        
        # 3. Process into RAG using the LLM logic
        print("Passing retrieved and scraped content to Local LLM...")
        llm = LLM(
            model_name=model_name,
            local_api_key=local_api_key,
            local_api_base=local_api_base
        )
        
        structured_report = llm.generate_company_report(
            company_name=request.company_name,
            region=request.company_region,
            retrieved_data=enriched_results
        )
        
        return structured_report

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if "No models loaded" in error_msg:
            raise HTTPException(status_code=500, detail="No models loaded in LM Studio. Please load a model (e.g., in the developer page or via 'lms load') and try again.")
        raise HTTPException(status_code=500, detail=error_msg)
