from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any
from unity_connection import get_unity_connection, send_command_with_retry
from config import config
import time
import os
import base64

def register_run_play_mode_tests_tools(mcp: FastMCP):
    """Register all play mode test runner tools with the MCP server."""

    @mcp.tool()
    def run_play_mode_tests(
        ctx: Context,
        action: str,
        test_assambly: str,
        test_clas: str,
        test_method: str,
    ) -> Dict[str, Any]:
        """Run play mode tests (start).

        Args:
            action: Operation ('run', 'status').
            test_assambly: The assambly specifified if an asambly, class or method is to be tested (default: "").
            test_clas: The class specifified if a class or method is to be tested (default: "").
            test_method: The method specifified if a method is to be tested (default: "")..

        Returns:
            Dictionary with results ('success', 'message', 'data').
        """
        try:
            # Prepare parameters for Unity
            params = {
                "action": action,
                "test_assambly": test_assambly,
                "test_clas": test_clas,
                "test_method": test_method,
            }
            
            # Remove None values so they don't get sent as null
            params = {k: v for k, v in params.items() if v is not None}

            # Send command via centralized retry helper
            response = send_command_with_retry("run_play_mode_tests", params)
            
            # Preserve structured failure data; unwrap success into a friendlier shape
            if isinstance(response, dict) and response.get("success"):
                return {"success": True, "message": response.get("message", "Scene operation successful."), "data": response.get("data")}
            return response if isinstance(response, dict) else {"success": False, "message": str(response)}

        except Exception as e:
            # Handle Python-side errors (e.g., connection issues)
            return {"success": False, "message": f"Python error managing shader: {str(e)}"}