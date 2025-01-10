from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, BackgroundTasks, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from .agent_manager import AgentManager
from .llm import OpenAIProvider, AnthropicProvider, OllamaProvider, DeepSeekProvider
import requests
import openai
import uuid
import anthropic

# Load environment variables
load_dotenv()

# Create artifacts directory if it doesn't exist
os.makedirs("artifacts", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(title="AgentX Assistant")

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.mount("/artifacts", StaticFiles(directory="artifacts"), name="artifacts")

# Configure templates
templates = Jinja2Templates(directory="src/templates")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat sessions
chat_sessions: Dict[str, AgentManager] = {}
active_requests: Dict[str, Any] = {}

# WebSocket connections
active_connections: Dict[str, Dict[str, Any]] = {}  # session_id -> {websocket, client_id}

async def broadcast_message(message: Dict[str, Any], session_id: str):
    """Broadcast message to the specific session"""
    if session_id in active_connections:
        try:
            await active_connections[session_id]["websocket"].send_json(message)
        except:
            # If sending fails, clean up the connection
            del active_connections[session_id]

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Handle WebSocket connections for chat"""
    await websocket.accept()
    
    # Close any existing connection for this session
    if session_id in active_connections:
        try:
            await active_connections[session_id]["websocket"].close()
        except:
            pass
    
    # Store new connection
    active_connections[session_id] = {
        "websocket": websocket,
        "client_id": str(uuid.uuid4())
    }
    
    try:
        while True:
            # Just keep the connection alive but don't process messages here
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Clean up connection on disconnect
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception:
        # Clean up on any other error
        if session_id in active_connections:
            del active_connections[session_id]

@app.post("/api/chat/new")
async def new_chat():
    """Start a new chat session"""
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = AgentManager(llm_provider=None, verbose=True)
    return {"session_id": session_id}

@app.post("/api/chat/cancel/{session_id}")
async def cancel_chat(session_id: str):
    """Cancel ongoing chat request"""
    if session_id in active_requests and active_requests[session_id]:
        agent = chat_sessions.get(session_id)
        if agent and agent.llm_provider:
            agent.llm_provider.cancel_request()
        active_requests[session_id] = None
    return {"status": "success"}

@app.get("/api/models/{provider}")
async def get_models(provider: str):
    """Get available models for a provider"""
    try:
        if provider == "ollama":
            # Get models from Ollama API
            response = requests.get("http://localhost:11434/api/tags")
            if response.ok:
                models = response.json()
                return [{"id": model["name"], "name": model["name"]} for model in models["models"]]
        elif provider == "openai":
            # Get models from OpenAI API
            client = openai.OpenAI()
            models = client.models.list()
            return [{"id": model.id, "name": model.id} for model in models.data 
                    if model.id.startswith(("gpt-4", "gpt-3.5"))]
        elif provider == "anthropic":
            # Get models from Anthropic API using their client
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
            client = anthropic.Anthropic(api_key=api_key)
            response = client.models.list(limit=100)
            
            models = []
            for model in response.data:
                models.append({
                    "id": model.id,
                    "name": model.display_name
                })
            
            return models
        elif provider == "deepseek":
            # Static list for DeepSeek
            return [
                {"id": "deepseek-coder", "name": "DeepSeek Coder"},
                {"id": "deepseek-chat", "name": "DeepSeek Chat"}
            ]
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/chat")
async def chat(message: Dict[str, Any], background_tasks: BackgroundTasks):
    """Process chat messages"""
    try:
        session_id = message.get("session_id")
        if not session_id or session_id not in chat_sessions:
            return {"status": "error", "message": "Invalid session ID"}

        # Check if we have an active WebSocket connection for this session
        if session_id not in active_connections:
            return {"status": "error", "message": "No active WebSocket connection"}

        agent_manager = chat_sessions[session_id]
        message_id = str(uuid.uuid4())
        
        # Get provider and model from request
        provider = message.get("provider")
        model = message.get("model")
        
        if not provider or not model:
            return {"status": "error", "message": "Provider and model must be selected"}
        
        # Create appropriate provider
        if provider == "ollama":
            llm_provider = OllamaProvider(model_name=model)
        elif provider == "openai":
            llm_provider = OpenAIProvider(model_name=model)
        elif provider == "anthropic":
            llm_provider = AnthropicProvider(model_name=model)
        elif provider == "deepseek":
            llm_provider = DeepSeekProvider(model_name=model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Update agent manager with new provider
        agent_manager.llm_provider = llm_provider
        
        # Set thinking state
        await broadcast_message({"type": "thinking", "value": True}, session_id)
        
        # Send user message to chat only once
        await broadcast_message({
            "type": "message",
            "content": {
                "id": f"user-{message_id}",
                "role": "user",
                "content": message["message"]
            }
        }, session_id)
        
        # Store active request
        active_requests[session_id] = llm_provider
        
        try:
            # Process request
            response = agent_manager.process_request(message["message"], stream=True)
            
            # Handle response based on type
            if hasattr(response, '__iter__') and not isinstance(response, str):
                # Streaming response
                full_response = ""
                for chunk in response:
                    if isinstance(chunk, str):
                        full_response += chunk
                        await broadcast_message({
                            "type": "message",
                            "content": {
                                "id": f"assistant-{message_id}",
                                "role": "assistant",
                                "content": full_response,
                                "is_streaming": True
                            }
                        }, session_id)
                
                # Send final streaming message
                if full_response:
                    await broadcast_message({
                        "type": "message",
                        "content": {
                            "id": f"assistant-{message_id}",
                            "role": "assistant",
                            "content": full_response,
                            "is_streaming": False
                        }
                    }, session_id)
            else:
                # Non-streaming response (e.g., final_answer)
                await broadcast_message({
                    "type": "message",
                    "content": {
                        "id": f"assistant-{message_id}",
                        "role": "assistant",
                        "content": str(response),
                        "is_streaming": False
                    }
                }, session_id)
        finally:
            # Clear active request
            active_requests[session_id] = None
            # Reset thinking state
            await broadcast_message({"type": "thinking", "value": False}, session_id)
        
        return {"status": "success"}
    except Exception as e:
        if session_id:
            active_requests[session_id] = None
        if session_id in active_connections:
            await broadcast_message({"type": "thinking", "value": False}, session_id)
            await broadcast_message({
                "type": "message",
                "content": {
                    "id": f"error-{uuid.uuid4()}",
                    "role": "assistant",
                    "content": f"Error: {str(e)}"
                }
            }, session_id)
        return {"status": "error", "message": str(e)}

@app.get("/api/tools")
async def get_tools():
    """Get available tools"""
    # Create a temporary agent manager without a provider
    temp_agent = AgentManager(llm_provider=None)
    return temp_agent.get_available_tools()

@app.get("/api/status")
async def get_status():
    """Get agent status"""
    # Create a temporary agent manager without a provider
    temp_agent = AgentManager(llm_provider=None)
    return temp_agent.get_agent_status()

@app.post("/api/provider")
async def update_provider(data: Dict[str, str]):
    """Update LLM provider"""
    provider = data["provider"]
    if provider == "OpenAI":
        llm_provider = OpenAIProvider()
    elif provider == "Anthropic":
        llm_provider = AnthropicProvider()
    else:
        return {"status": "error", "message": "Unsupported provider"}
    
    temp_agent = AgentManager(llm_provider=OpenAIProvider())
    temp_agent.update_configuration(llm_provider=llm_provider)
    return {"status": "success"}

@app.post("/api/chat/clear")
async def clear_chat():
    """Clear chat history"""
    return {"status": "success"}

@app.post("/api/image/generate")
async def generate_image(request: Dict[str, Any]):
    """Generate an image using the selected model"""
    try:
        provider = request.get("provider")
        prompt = request.get("prompt")
        size = request.get("size", "1024x1024")
        
        if not prompt:
            raise ValueError("Prompt is required")
            
        # Validate image size
        valid_sizes = ["256x256", "512x512", "1024x1024"]
        if size not in valid_sizes:
            raise ValueError(f"Invalid size. Supported sizes are: {', '.join(valid_sizes)}")
        
        if provider == "openai":
            client = openai.OpenAI()
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )
            return {"url": response.data[0].url}
        else:
            raise ValueError(f"Unsupported provider for image generation: {provider}")
            
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/web/search")
async def web_search(request: Dict[str, Any]):
    """Perform web search"""
    try:
        query = request.get("query")
        if not query:
            raise ValueError("Search query is required")
            
        # Implement web search functionality
        # This is a placeholder - implement actual web search integration
        return {"results": []}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/artifacts/create")
async def create_artifact(file: UploadFile):
    """Create a new artifact from uploaded file"""
    try:
        # Create artifacts directory if it doesn't exist
        os.makedirs("artifacts", exist_ok=True)
        
        # Save file
        file_path = f"artifacts/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Return file URL
        return {
            "status": "success",
            "url": f"/artifacts/{file.filename}",
            "name": file.filename
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/artifacts/list")
async def list_artifacts():
    """List available artifacts"""
    try:
        # Create artifacts directory if it doesn't exist
        os.makedirs("artifacts", exist_ok=True)
        
        # List files in artifacts directory
        files = os.listdir("artifacts")
        artifacts = []
        for file in files:
            artifacts.append({
                "name": file,
                "url": f"/artifacts/{file}"
            })
        return {"artifacts": artifacts}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 