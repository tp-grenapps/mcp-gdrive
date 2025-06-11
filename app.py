from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

from gdrive import GoogleDriveAPI

# Initialize FastMCP server
mcp = FastMCP("gdrive")
# mcp = FastMCP(name="gdrive", host="127.0.0.1", port="8123")

# gdrive = GoogleDriveAPI()

@mcp.tool()
async def list_files(state: str) -> str:
    """List all the files in Google Drive account.
    """
    gdrive = GoogleDriveAPI()
    print("listing files ..")
    return gdrive.list_files()

@mcp.tool()
async def search_files(state: str) -> str:
    """Search files in Google Drive account.

    Args:
        name: name of files to be searched
    """
    gdrive = GoogleDriveAPI()
    print("searching files ...")
    return "searching files ..."


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')