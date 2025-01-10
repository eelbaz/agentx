from typing import List, Dict, Any, Optional, Type
import logging
from smolagents import CodeAgent, Tool
from .llm import LLMProvider, OpenAIProvider
from .tools.base_tools import (
    WebSearchTool,
    WebScrapeTool,
    SystemCommandTool,
    FileSystemTool,
    TwitterSearchTool,
    SystemInfoTool
)

# Configure logging
logger = logging.getLogger("agent_manager")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class AgentManager:
    """Manages agent configuration and execution"""
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        max_steps: int = 10,
        verbose: bool = False,
        additional_tools: Optional[List[Tool]] = None,
        additional_imports: Optional[List[str]] = None
    ):
        self.llm_provider = llm_provider or OpenAIProvider()
        self.max_steps = max_steps
        self.verbose = verbose
        
        # Initialize default tools
        self.tools = [
            WebSearchTool(),
            WebScrapeTool(),
            SystemCommandTool(),
            FileSystemTool(),
            TwitterSearchTool(),
            SystemInfoTool()
        ]
        
        # Add any additional tools
        if additional_tools:
            self.tools.extend(additional_tools)
            
        # Set up authorized imports
        self.authorized_imports = {
            'os', 'sys', 'json', 'time', 'datetime', 'math', 
            'random', 'requests', 'numpy', 'pandas'
        }
        if additional_imports:
            self.authorized_imports.update(additional_imports)
            
        # Initialize the agent
        self.agent = self._initialize_agent()
        
    def _initialize_agent(self) -> CodeAgent:
        """Initialize the agent with current configuration"""
        logger.info("Initializing CodeAgent")
        return CodeAgent(
            tools=self.tools,
            model=self.llm_provider,
            max_steps=self.max_steps,
            verbose=self.verbose,
            additional_authorized_imports=list(self.authorized_imports)
        )

    def add_tool(self, tool: Tool) -> None:
        """Add a new tool to the agent's toolset"""
        self.tools.append(tool)
        self.agent = self._initialize_agent()

    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent's toolset"""
        self.tools = [t for t in self.tools if t.name != tool_name]
        self.agent = self._initialize_agent()

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get information about available tools"""
        return [{
            'name': tool.name,
            'description': tool.description,
            'inputs': tool.inputs,
            'output_type': tool.output_type
        } for tool in self.tools]

    def process_request(
        self,
        request: str,
        stream: bool = False,
        additional_args: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Process a user request using the agent"""
        try:
            return self.agent.run(
                request,
                stream=stream,
                additional_args=additional_args or {}
            )
        except Exception as e:
            return {
                'error': True,
                'message': f"Error processing request: {str(e)}"
            }

    def update_configuration(
        self,
        llm_provider: Optional[LLMProvider] = None,
        max_steps: Optional[int] = None,
        verbose: Optional[bool] = None,
        additional_imports: Optional[List[str]] = None
    ) -> None:
        """Update the agent's configuration"""
        if llm_provider:
            self.llm_provider = llm_provider
        if max_steps is not None:
            self.max_steps = max_steps
        if verbose is not None:
            self.verbose = verbose
        if additional_imports:
            self.authorized_imports.update(additional_imports)
        self.agent = self._initialize_agent()

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current status of the agent"""
        return {
            'llm_provider': self.llm_provider.__class__.__name__,
            'num_tools': len(self.tools),
            'max_steps': self.max_steps,
            'verbose': self.verbose,
            'authorized_imports': sorted(list(self.authorized_imports))
        } 