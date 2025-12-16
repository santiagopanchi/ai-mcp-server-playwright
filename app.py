import asyncio
import inspect
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
import os

load_dotenv(override=True)

async def main():

    playwright_params = {"command": "npx","args": [ "-y", "@playwright/mcp@latest"]}
    playwright_server_instance = MCPServerStdio(params=playwright_params)
    async with playwright_server_instance as server:
        playwright_tools = await server.session.list_tools()

    files_params = {"command": "uv", "args": ["run", "simple_files_server.py"]}
    files_server_instance = MCPServerStdio(params=files_params)
    async with files_server_instance as server:
        file_tools = await server.session.list_tools()

    instructions = """
    You browse content available at https://www.domain.com.au/ to accomplish your instructions.
    You are highly capable at browsing the internet independently to accomplish your task, 
    including accepting all cookies and clicking 'not now' as
    appropriate to get to the content you need. 
    Be persistent until you have solved your assignment,
    trying different options and sites as needed.
    Use the \"try a location or a school or project name\" textfield to search for the property.
    """

    mcp_server_params = [files_params, playwright_params]
    
    async with AsyncExitStack() as stack:
        mcp_servers = [
            await stack.enter_async_context(MCPServerStdio(params=params))
            for params in mcp_server_params
        ]
        agent = Agent(
            name="investigator", 
            instructions=instructions, 
            model="gpt-4.1-mini",
            mcp_servers=mcp_servers
        )
        with trace("investigate"):
            result = await Runner.run(agent, "Find all property features of 185 Wharf St and then summarize it in markdown to property.md")
            print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())