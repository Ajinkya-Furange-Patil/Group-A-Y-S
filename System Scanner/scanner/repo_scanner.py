"""
AI Repository Scanner MVP — Remote Repository Scan Engine

Responsible for downloading public GitHub repository ZIP archives, extracting them,
and recursively scanning source files and configuration assets to detect:
  1. Languages
  2. Dependencies/Frameworks
  3. AI Models
  4. Heuristic AI Components (LLM, SLM, Agent, RAG, MCP, etc.)
  5. Confidence scoring (30% for deps, 70% for deps+code, 95% for deps+code+config)
"""

import json
import logging
import os
import re
import shutil
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from scanner.status_tracker import update_scan_status

logger = logging.getLogger(__name__)

# Pinned Dependency Keywords for Scanning
PYTHON_DEPS = [
    "openai", "langchain", "langgraph", "crewai", "autogen", "transformers",
    "torch", "tensorflow", "sentence-transformers", "llama-index", "anthropic",
    "google-generativeai", "chromadb", "faiss", "qdrant-client", "pinecone"
]

NODEJS_DEPS = [
    "openai", "langchain", "@langchain/core", "@anthropic-ai/sdk", "@google/generative-ai"
]

# Code Pattern Detections per Category
CODE_PATTERNS = {
    "LLM": [r"OpenAI\(", r"ChatOpenAI\(", r"Anthropic\(", r"GenerativeModel\("],
    "Agent": [r"AgentExecutor\(", r"Crew\(", r"AssistantAgent\(", r"UserProxyAgent\(", r"StateGraph\("],
    "RAG": [r"similarity_search\(", r"retriever", r"embedding", r"embeddings", r"vectorstore"],
    "MCP": [r"mcp", r"tool_registry", r"tool_schema", r"register_tool"],
    "SLM": [r"AutoModelForCausalLM\.from_pretrained\(", r"Ollama\(model=", r"phi-3", r"qwen-2", r"llama3\.2", r"llama3\.1"],
    "Agentic Workflow": [r"StateGraph\(", r"Workflow\(", r"workflow\.add_node", r"LangGraph"],
    "Embeddings": [r"OpenAIEmbeddings", r"HuggingFaceEmbeddings", r"SentenceTransformer"],
    "Vector Database": [r"chromadb", r"Pinecone\(", r"qdrant", r"faiss\.Index"],
    "Inference Engine": [r"Ollama\(", r"vllm", r"llama_cpp", r"llama\.cpp"],
    "Fine Tuning": [r"LoraConfig\(", r"peft", r"SFTTrainer", r"TrainingArguments"],
    "AI SDK": [r"import openai", r"import anthropic", r"import google\.generativeai", r"require\(['\"]openai['\"]\)", r"require\(['\"]@langchain/core['\"]\)"],
    "Prompt Engineering": [r"PromptTemplate", r"SystemMessage", r"system_prompt", r"PromptTemplate\.from_template"]
}

# Model Name Keywords (Case Insensitive)
MODEL_KEYWORDS = ["gpt-4", "gpt-4o", "gpt-5", "gemini", "claude", "llama", "mistral", "deepseek", "phi", "qwen"]

# Configuration File Indicators
CONFIG_PATTERNS = [
    "mcp-config.json", "mcp_config.json", "config.yaml", "config.json",
    ".env", ".env.example", ".env.template"
]

# File Extension to Friendly Language Name Mapping
LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".jsx": "React (JS)",
    ".tsx": "React (TS)",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".h": "C/C++ Header",
    ".c": "C",
    ".sh": "Shell Script",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".md": "Markdown"
}


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Parse a GitHub URL and return (owner, repo_name) or None if invalid."""
    url = url.strip()
    # Normalize trailing slashes and .git suffix
    if url.endswith(".git"):
        url = url[:-4]
    if url.endswith("/"):
        url = url[:-1]
        
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        return owner, repo
    return None


def download_repo_zip(owner: str, repo: str, dest_dir: str) -> str | None:
    """Download repository ZIP file from GitHub with fallback to master branch."""
    os.makedirs(dest_dir, exist_ok=True)
    zip_path = os.path.join(dest_dir, f"{owner}_{repo}.zip")
    
    # Try heads/main.zip first
    main_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
    master_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for url in [main_url, master_url]:
        try:
            logger.info("Attempting download from URL: %s", url)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(zip_path, "wb") as out_file:
                    out_file.write(response.read())
            logger.info("Successfully downloaded repository ZIP to %s", zip_path)
            return zip_path
        except urllib.error.HTTPError as e:
            logger.warning("Failed downloading from %s: %s", url, e)
            continue
        except Exception as e:
            logger.error("Download failed: %s", e)
            continue
            
    return None


def extract_zip(zip_path: str, extract_to: str) -> str | None:
    """Extract zip archive and return path to the extracted repository folder."""
    try:
        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            
        # Locate the root subdirectory created inside extraction folder
        entries = os.listdir(extract_to)
        for entry in entries:
            full_path = os.path.join(extract_to, entry)
            if os.path.isdir(full_path):
                logger.info("Extracted repository folder: %s", full_path)
                return full_path
        return extract_to
    except Exception as e:
        logger.error("Failed to extract ZIP: %s", e)
        return None


def scan_repository(repo_path: str, repo_url: str) -> dict:
    """Scan directory recursively for AI footprint, code patterns, and dependencies using standard ScanController."""
    from scanner.controller import ScanController
    from scanner.models import FindingCategory
    
    # 1. Determine languages in repo by walking it
    languages_found = set()
    for root, dirs, files in os.walk(repo_path):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "env", "dist", "build", "__pycache__"}]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in LANGUAGE_MAP:
                languages_found.add(LANGUAGE_MAP[ext])
                
    # 2. Run ScanController
    controller = ScanController(quick=False, scan_folder=repo_path)
    result = controller.run_scan()
    
    # 3. Extract frameworks, models, components, findings
    frameworks_found = set()
    models_found = set()
    components_found = set()
    findings = []
    
    has_dep = False
    has_code = False
    has_config = False
    
    for f in result.findings:
        # Ignore system/process/runtime findings since they reflect the scanner's host OS, not the repo itself
        if f.module_name in ["SystemScanner", "ProcessScanner", "RuntimeScanner"]:
            continue
            
        # Get relative path for findings
        rel_file = f.details.get("file_path") or f.source
        # Extract file path if format is path:line
        if ":" in rel_file:
            parts = rel_file.split(":")
            # In Windows, a path can have drive prefix C:, so we handle it
            if len(parts) > 2 and len(parts[0]) == 1:
                rel_file = ":".join(parts[:-1])
            else:
                rel_file = parts[0]
        
        # If absolute, make relative to repo_path
        if os.path.isabs(rel_file):
            try:
                rel_file = os.path.relpath(rel_file, repo_path).replace("\\", "/")
            except ValueError:
                rel_file = os.path.basename(rel_file)
        else:
            rel_file = rel_file.replace("\\", "/")
            
        line_num = f.details.get("line_number") or 1
        
        # Extract framework name if it was a package finding
        if f.module_name == "PackageScanner":
            has_dep = True
            pkg_name = f.details.get("package_name") or f.title.replace("Dependency: ", "").replace("NPM Dependency: ", "")
            if pkg_name:
                # clean version suffix if any
                pkg_name = pkg_name.split()[0].split("(")[0].strip()
                frameworks_found.add(pkg_name.lower())
                
        # Look for model names
        # Check details or title for model keywords
        for m in MODEL_KEYWORDS:
            if re.search(rf"\b{re.escape(m)}\b", f.title + " " + f.description, re.IGNORECASE):
                models_found.add(m)
                
        # Look for configuration findings
        if f.module_name == "MCPScanner" or f.category == FindingCategory.CONFIGURATION:
            has_config = True
            
        # Code usage checking
        if f.module_name == "AgentScanner":
            has_code = True
            
        # Map categories/components
        matched_pattern = f.details.get("matched_pattern") or ""
        found_category = "AI SDK"
        title_lower = f.title.lower()
        desc_lower = f.description.lower()
        
        # Try to classify component category
        if "agent" in title_lower or "agent" in desc_lower or "crew" in title_lower or "autogen" in title_lower:
            found_category = "Agent"
        elif "rag" in title_lower or "similarity_search" in desc_lower or "vector" in desc_lower or "embed" in desc_lower:
            found_category = "RAG"
        elif "mcp" in title_lower or "mcp" in desc_lower:
            found_category = "MCP"
        elif "openai" in title_lower or "anthropic" in title_lower or "generativeai" in title_lower:
            found_category = "AI SDK"
        
        # Let's also look at matched_pattern to override category
        for cat in CODE_PATTERNS.keys():
            if cat.lower() in matched_pattern.lower() or cat.lower() in title_lower:
                found_category = cat
                
        components_found.add(found_category)
        
        findings.append({
            "file": rel_file,
            "line": line_num,
            "category": found_category,
            "matched_pattern": matched_pattern or f.title,
            "snippet": f.details.get("snippet") or f.description[:120]
        })
        
    # Check config files in the repo root directly to ensure has_config detection matches spec
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "env"}]
        for file in files:
            if file in CONFIG_PATTERNS:
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().upper()
                        if any(kw in content for kw in ["API_KEY", "OPENAI", "ANTHROPIC", "GEMINI", "LLM", "MODEL", "PORT", "MCP"]):
                            has_config = True
                except Exception:
                    pass
                    
    # Calculate confidence score based on the rules
    confidence_score = 0
    if has_dep:
        confidence_score = 30
        if has_code:
            confidence_score = 70
            if has_config:
                confidence_score = 95
    elif has_code:
        confidence_score = 50
        if has_config:
            confidence_score = 75
            
    if has_config:
        components_found.add("Configuration")
        
    return {
        "repository": repo_url,
        "languages": sorted(list(languages_found)),
        "frameworks": sorted(list(frameworks_found)),
        "models": sorted(list(models_found)),
        "components": sorted(list(components_found)),
        "findings": findings,
        "confidence_score": confidence_score
    }


def run_repo_scan(repo_url: str) -> dict | None:
    """Download, extract, and scan the remote GitHub repository."""
    logger.info("Starting Remote Repository Scan workflow for: %s", repo_url)
    
    parsed = parse_github_url(repo_url)
    if not parsed:
        logger.error("Invalid GitHub Repository URL: %s", repo_url)
        update_scan_status("Error: Invalid URL", 100)
        return None
        
    owner, repo = parsed
    logger.info("Extracted Owner: %s, Repository: %s", owner, repo)
    
    # Workspace directories (local inside project)
    workspace_root = Path(os.getcwd())
    temp_dir = workspace_root / "temp_repos"
    timestamp = int(time.time())
    scan_temp_folder = temp_dir / f"{owner}_{repo}_{timestamp}"
    extract_folder = scan_temp_folder / "extracted"
    
    try:
        # Step 1: Download
        update_scan_status("Downloading Repository...", 15)
        zip_path = download_repo_zip(owner, repo, str(scan_temp_folder))
        if not zip_path:
            logger.error("Failed to download ZIP for %s/%s", owner, repo)
            update_scan_status("Error: Download Failed", 100)
            return None
            
        # Step 2: Extract
        update_scan_status("Extracting Contents...", 35)
        extracted_path = extract_zip(zip_path, str(extract_folder))
        if not extracted_path:
            logger.error("Failed to extract ZIP for %s/%s", owner, repo)
            update_scan_status("Error: Extraction Failed", 100)
            return None
            
        # Step 3: Scan
        update_scan_status("Scanning Dependencies...", 60)
        report_data = scan_repository(extracted_path, repo_url)
        
        # Step 4: Finalize
        update_scan_status("Finalizing Results...", 95)
        
        # Cleanup zip to save workspace space (leave folder for inspection or let it clean up on next scan)
        try:
            os.remove(zip_path)
            # Remove full temp folder after reporting to keep repository clean
            shutil.rmtree(scan_temp_folder, ignore_errors=True)
        except Exception as e:
            logger.debug("Failed during files cleanup: %s", e)
            
        update_scan_status("Complete", 100)
        return report_data
        
    except Exception as e:
        logger.error("Repository scan process crashed: %s", e, exc_info=True)
        update_scan_status(f"Error: {e}", 100)
        return None
