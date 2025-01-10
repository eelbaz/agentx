from typing import Optional, List, Dict, Any
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import subprocess
import os
import psutil
import tweepy
from smolagents import Tool

class WebSearchTool(Tool):
    """DuckDuckGo search tool implementation"""
    name = "web_search"
    description = "Search the web using DuckDuckGo"
    inputs = {
        "query": {
            "type": "string",
            "description": "The search query to perform"
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "default": 5,
            "nullable": True
        }
    }
    output_type = "string"

    def forward(self, query: str, max_results: int = 5) -> str:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return str(results)

class WebScrapeTool(Tool):
    """Web scraping tool implementation"""
    name = "web_scrape"
    description = "Scrape content from a webpage"
    inputs = {
        "url": {
            "type": "string",
            "description": "The URL to scrape"
        }
    }
    output_type = "string"

    def forward(self, url: str) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text()
        except Exception as e:
            return f"Error scraping webpage: {str(e)}"

class SystemCommandTool(Tool):
    """System command execution tool"""
    name = "system_command"
    description = "Execute system commands (use with caution)"
    inputs = {
        "command": {
            "type": "string",
            "description": "The command to execute"
        }
    }
    output_type = "string"

    def forward(self, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.stdout else result.stderr
        except Exception as e:
            return f"Error executing command: {str(e)}"

class FileSystemTool(Tool):
    """File system operations tool"""
    name = "file_system"
    description = "Perform file system operations"
    inputs = {
        "operation": {
            "type": "string",
            "description": "Operation to perform (read/write/list)",
            "enum": ["read", "write", "list"]
        },
        "path": {
            "type": "string",
            "description": "File or directory path"
        },
        "content": {
            "type": "string",
            "description": "Content to write (for write operation)",
            "nullable": True
        }
    }
    output_type = "string"

    def forward(self, operation: str, path: str, content: Optional[str] = None) -> str:
        try:
            if operation == "read":
                with open(path, 'r') as f:
                    return f.read()
            elif operation == "write":
                with open(path, 'w') as f:
                    f.write(content)
                return f"Successfully wrote to {path}"
            elif operation == "list":
                return str(os.listdir(path))
        except Exception as e:
            return f"Error performing file operation: {str(e)}"

class TwitterSearchTool(Tool):
    """Twitter search tool implementation"""
    name = "twitter_search"
    description = "Search Twitter for recent tweets"
    inputs = {
        "query": {
            "type": "string",
            "description": "The search query"
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of tweets to return",
            "default": 10,
            "nullable": True
        }
    }
    output_type = "string"

    def __init__(self):
        self.api = None
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        if all([api_key, api_secret, access_token, access_token_secret]):
            try:
                auth = tweepy.OAuthHandler(api_key, api_secret)
                auth.set_access_token(access_token, access_token_secret)
                self.api = tweepy.API(auth)
            except Exception as e:
                print(f"Error initializing Twitter API: {str(e)}")

    @property
    def is_initialized(self) -> bool:
        """Check if the Twitter API is properly initialized"""
        return self.api is not None

    def forward(self, query: str, max_results: int = 10) -> str:
        if not self.is_initialized:
            return "Twitter API is not configured. Please set the required environment variables: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET"
        
        try:
            tweets = self.api.search_tweets(q=query, count=max_results)
            results = [{
                'text': tweet.text,
                'user': tweet.user.screen_name,
                'created_at': str(tweet.created_at)
            } for tweet in tweets]
            return str(results)
        except Exception as e:
            return f"Error searching Twitter: {str(e)}"

class SystemInfoTool(Tool):
    """System information tool"""
    name = "system_info"
    description = "Get system information and metrics"
    inputs = {
        "metric": {
            "type": "string",
            "description": "Metric to retrieve (cpu/memory/disk)",
            "enum": ["cpu", "memory", "disk"]
        }
    }
    output_type = "string"

    def forward(self, metric: str) -> str:
        try:
            if metric == "cpu":
                info = {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "cpu_count": psutil.cpu_count(),
                    "cpu_freq": psutil.cpu_freq()._asdict()
                }
            elif metric == "memory":
                mem = psutil.virtual_memory()
                info = {
                    "total": mem.total,
                    "available": mem.available,
                    "percent": mem.percent
                }
            elif metric == "disk":
                disk = psutil.disk_usage('/')
                info = {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                }
            return str(info)
        except Exception as e:
            return f"Error getting system info: {str(e)}" 