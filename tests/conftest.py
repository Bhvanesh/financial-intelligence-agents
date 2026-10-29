import os
import sys
from unittest.mock import MagicMock

# Set env vars before any imports
os.environ["DATABASE_URL"]          = "sqlite+pysqlite:///:memory:"
os.environ["OPENAI_MODEL"]          = "gpt-4o-mini"
os.environ["OPENAI_API_KEY"]        = "test-openai-key"
os.environ["LANGCHAIN_TRACING_V2"]  = "false"
os.environ["LANGCHAIN_API_KEY"]     = ""
os.environ["REDIS_HOST"]            = "localhost"
os.environ["REDIS_PORT"]            = "6379"
os.environ["REDIS_DB"]              = "0"

# Mock heavy dependencies
sys.modules["redis"]                       = MagicMock()
sys.modules["langchain_openai"]            = MagicMock()
sys.modules["langchain_core"]              = MagicMock()
sys.modules["langchain_core.tools"]        = MagicMock()
sys.modules["langchain_core.messages"]     = MagicMock()
sys.modules["langchain_core.callbacks"]    = MagicMock()
sys.modules["langchain_community"]         = MagicMock()
sys.modules["langchain_community.document_loaders"] = MagicMock()
sys.modules["langchain_text_splitters"]    = MagicMock()
sys.modules["langchain_chroma"]            = MagicMock()
sys.modules["rank_bm25"]                   = MagicMock()
sys.modules["langgraph"]                   = MagicMock()
sys.modules["langgraph.graph"]             = MagicMock()
sys.modules["pypdf"]                       = MagicMock()
sys.modules["graph"]                       = MagicMock()
sys.modules["pdf_loader"]                  = MagicMock()