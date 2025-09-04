from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any
from unity_connection import get_unity_connection, send_command_with_retry
from config import config
import time
import os
import base64

def register_your_tool_tools(mcp: FastMCP):
    """Register all your tools with the MCP server."""

    @mcp.tool()
    def your_tool(
        ctx: Context,
        action: str,
        input_parm1: str,
        input_param2: str,
        input_param3: str,
    ) -> Dict[str, Any]:
        """your tool function discribed to the AI.

        Args:
            action: Operation ('action1', 'action2').
            input_param1: Explain what is expected and default can be specified like this (defsult ””) 
            input_param2: Explain what is expected and default can be specified like this (defsult ””) 
            input_param3: Explain what is expected and default can be specified like this (defsult ””) 

        Returns:
            Dictionary with results ('success', 'message', 'data').
        """
        try:
            # Prepare parameters for Unity
            params = {
                "action": action,
                "inptu_param1": inptu_param1,
                "inptu_param2": inptu_param2,
                "inptu_param3": inptu_param3,
            }
            
            # Remove None values so they don't get sent as null
            params = {k: v for k, v in params.items() if v is not None}

            # Send command via centralized retry helper
            response = send_command_with_retry("your_tool", params)
            
            # Preserve structured failure data; unwrap success into a friendlier shape
            if isinstance(response, dict) and response.get("success"):
                return {"success": True, "message": response.get("message", "YourTool operation successful."), "data": response.get("data")}
            return response if isinstance(response, dict) else {"success": False, "message": str(response)}

        except Exception as e:
            # Handle Python-side errors (e.g., connection issues)
            return {"success": False, "message": f"Python error managing shader: {str(e)}"}