import os
import asyncio
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from agents import Agent, Runner, trace, Tool
from agents.mcp import MCPServerStdio
from IPython.display import Markdown, display
from datetime import datetime

load_dotenv(override=True)


async def get_researcher(mcp_servers) -> Agent:
    instructions = f"""You are a financial researcher. You are able to search the web for interesting financial news,
look for possible trading opportunities, and help with research.
Based on the request, you carry out necessary research and respond with your findings.
Take time to make multiple searches to get a comprehensive overview, and then summarize your findings.
If there isn't a specific request, then just respond with investment opportunities based on searching latest news.
The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    researcher = Agent(
        name="Researcher",
        instructions=instructions,
        model="gpt-4.1-mini",
        mcp_servers=mcp_servers,
    )
    return researcher

async def main():
    # Get Brave API key from environment
    brave_api_key = os.getenv("BRAVE_API_KEY")
    if not brave_api_key:
        raise ValueError("BRAVE_API_KEY environment variable is not set")
    
    brave_env = {"BRAVE_API_KEY": brave_api_key}

    # Configure MCP server parameters
    researcher_mcp_server_params = [
        {   "command": "uvx",
            "args": ["mcp-server-fetch"]
        },
        {   "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env
        },
        # {
        #     "command": "npx",
        #     "args": ["-y", "mcp-memory-libsql"],
        #     "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
        # },
    ]

    # Use AsyncExitStack to manage MCP server contexts
    async with AsyncExitStack() as stack:
        # Create MCP server connections using async context manager
        # Try to use longer timeout if supported, otherwise use default
        try:
            # Check if client_session_timeout_seconds parameter is supported
            import inspect
            sig = inspect.signature(MCPServerStdio.__init__)
            if 'client_session_timeout_seconds' in sig.parameters:
                researcher_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params
                ]
            else:
                researcher_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params)
                    )
                    for params in researcher_mcp_server_params
                ]
        except Exception:
            # Fallback to default if anything goes wrong
            researcher_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params)
                )
                for params in researcher_mcp_server_params
            ]

        # Create the researcher agent with MCP servers
        researcher = await get_researcher(researcher_mcp_servers)

        # Example: Run a research query
        query = "What are the latest trends in AI and machine learning investments?"
        print(f"Running query: {query}\n")
        
        # Use Runner.run() as a class method
        response = await Runner.run(researcher, query, max_turns=30)
        print("\n" + "="*80)
        print("RESEARCH RESULTS:")
        print("="*80)
        # Get the final output as a string
        output = response.final_output_as(str)
        print(output)
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
