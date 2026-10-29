import os
import uuid
import logging
import time
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from api_key_manager import generate_api_key, validate_api_key, is_rate_limited
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from database import Base, engine, get_db
from models import Analysis, APIKey
from schemas import  AnalysisResponse, AnalysisSummaryResponse, MetricsOnlyResponse, RisksOnlyResponse, TrendsResponse, SummaryResponse, FullAnalysisResponse, APIKeyRegisterRequest, APIKeyResponse
from pdf_loader import load_pdf_text
from graph import graph

load_dotenv(override = False)

import os

os.environ["LANGCHAIN_TRACING_V2"]  = os.getenv("LANGCHAIN_TRACING_V2", "false")
os.environ["LANGCHAIN_API_KEY"]     = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"]     = os.getenv("LANGCHAIN_PROJECT", "Multi_Agent_System")
os.environ["LANGCHAIN_ENDPOINT"]    = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

logging.basicConfig(level = logging.INFO, format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt = "%y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Earnings Report Analyzer API",
    description="Multi-agent financial document analysis using LangGraph",
    version="1.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
api_key_header = APIKeyHeader(name="X-API-Key", description="API key required for POST /analyze", auto_error=False)
Base.metadata.create_all(bind=engine)


def get_api_key(api_key: str = Security(api_key_header), db: Session = Depends(get_db)) -> APIKey:
    """
    Dependency — validates API key from request header.
    Raises 401 if missing or invalid.
    Raises 429 if rate limited.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Include X-API-Key header."
        )        

    db_key = validate_api_key(api_key, db)
    if not db_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key."
        )

    limited, count, ttl = is_rate_limited(api_key, limit=3, window=60)
    if limited:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum 10 requests per minute. Retry in {ttl} seconds."
        )

    return db_key

@app.post("/register", response_model=APIKeyResponse)
async def register(request: APIKeyRegisterRequest, db: Session = Depends(get_db)):
    """
    Register and receive an API key.
    Store the key safely — it will be shown only once.
    """
    try:
        key = generate_api_key()
        api_key = APIKey(key = key, owner_name = request.owner_name, is_active = True)
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        logger.info(f"API key registered | owner: {request.owner_name} | key: {key[:8]}...")
        return api_key
    except Exception as e:
        logger.error(f"Error registering API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))





def _build_response(analysis) -> dict:
     """Returns only the fields relevant to the route.No null fields in the response."""
     base = {
        "id":           analysis.id,
        "filename":     analysis.filename,
        "user_prompt":  analysis.user_prompt,
        "route":        analysis.route,
        "created_at":   analysis.created_at.isoformat(),
    }
     if analysis.route == "metrics_only":
        return {
            **base,
            "company_name":  analysis.company_name,
            "fiscal_period": analysis.fiscal_period,
            "metrics":       analysis.metrics,
        }

     elif analysis.route == "risks_only":
        return {
            **base,
            "risks": analysis.risks,
        }

     elif analysis.route == "metrics_and_analysis":
        return {
            **base,
            "company_name":  analysis.company_name,
            "fiscal_period": analysis.fiscal_period,
            "metrics":       analysis.metrics,
            "analysis":      analysis.analysis,
        }

     elif analysis.route == "summary_only":
        return {
            **base,
            "company_name":  analysis.company_name,
            "fiscal_period": analysis.fiscal_period,
            "metrics":       analysis.metrics,
            "analysis":      analysis.analysis,
            "report":        analysis.report,
        }

     else:  # full_analysis
        return {
            **base,
            "company_name":  analysis.company_name,
            "fiscal_period": analysis.fiscal_period,
            "metrics":       analysis.metrics,
            "analysis":      analysis.analysis,
            "risks":         analysis.risks,
            "report":        analysis.report,
        }


MAX_FILE_SIZE = 10 * 1024 *1024
MAX_PROMPT_LENGTH = 500

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...), user_prompt: str = Form(...), db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        logger.info(
            f"Analysis request | owner: {api_key.owner_name} | "
            f"file: {file.filename} | prompt: {user_prompt}"
        )
        if len(user_prompt.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="user_prompt cannot be empty"
            )

        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code = 400, detail="Only PDF files are allowed.")
        
        contents = await file.read()
        
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code = 400, detail = f"File size : {len(contents)} exceeds the maximum limit of 10 MB.")

        if len(user_prompt) > MAX_PROMPT_LENGTH:
            raise HTTPException(status_code = 400, detail = f"Prompt length : {len(user_prompt)} exceeds the maximum limit of {MAX_PROMPT_LENGTH} characters.")
        
        safe_filename = f"{uuid.uuid4().hex}.pdf"
        temp_path = f"./uploads/{safe_filename}"

        os.makedirs("./uploads", exist_ok = True)
        with open(temp_path, "wb") as f:
            f.write(contents)

        logger.info(f"File uploaded: {file.filename} | Prompt: {user_prompt} | API Key: {api_key.key[:8]}...")
        start_time = time.time()
        report_text = load_pdf_text(temp_path)
        result = graph.invoke({"report_text": report_text,
            "user_prompt": user_prompt,
            "route":       None,
            "metrics":     None,
            "analysis":    None,
            "risks":       None,
            "report":      None,
        })

        logger.info(f"Route taken : {result['route']}")

        metrics = result['metrics']
        company_name = metrics.get("company_name") if metrics else None
        fiscal_period = metrics.get("fiscal_period") if metrics else None
        latency = round(time.time() - start_time, 2)

        analysis = Analysis(
            filename = file.filename,
            user_prompt = user_prompt,
            route = result['route'],
            company_name = company_name,
            fiscal_period = fiscal_period,
            metrics = metrics,
            analysis = result['analysis'],
            risks = result['risks'],
            report = result['report'],
            created_at = datetime.utcnow(),    
            latency_seconds = latency    
        )

        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        os.remove(temp_path)

        logger.info(f"Analysis saved: {analysis.id}")

        return JSONResponse(content=_build_response(analysis))
 
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An error occurred during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during analysis.")

@app.get("/all_analyses", response_model = list[AnalysisSummaryResponse])
async def list_analyses(db: Session =Depends(get_db)):
    try:
        analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
        logger.info(f"List of document analyses retrieved: {len(analyses)}")
        return analyses
    except Exception as e:
        logger.error(f"An error occurred while listing analyses: {str(e)}")
        raise HTTPException(status_code = 500, detail = "An error occurred while listing analyses.")

@app.get("/analysis/{id}")
async def get_analysis(id : int, db : Session = Depends(get_db)):
    try:
        analysis = db.query(Analysis).filter(Analysis.id ==id).first()
        if not analysis:
            raise HTTPException(status_code = 404, detail = "Analysis not found")
        logger.info(f"Analysis retrieved: {analysis}")
        return JSONResponse(content= _build_response(analysis))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An error occurred while retrieving analysis: {str(e)}")
        raise HTTPException(status_code = 500, detail = "An error occurred while retrieving analysis.")

    

