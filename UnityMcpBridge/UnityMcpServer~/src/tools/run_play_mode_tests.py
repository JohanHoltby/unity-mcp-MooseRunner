from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any
from unity_connection import get_unity_connection, send_command_with_retry
from config import config
import time
import os
import base64
import logging

logger = logging.getLogger("mcp-for-unity-server")

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
            if action == "status":
                # Pass through status request
                response = send_command_with_retry("run_play_mode_tests", {"action": "status"})
                
                # Preserve structured failure data; unwrap success into a friendlier shape
                if isinstance(response, dict) and response.get("success"):
                    return {"success": True, "message": response.get("message", "Status retrieved"), "data": response.get("data")}
                return response if isinstance(response, dict) else {"success": False, "message": str(response)}
                
            elif action == "run":
                # Start test execution
                params = {
                    "action": "run",
                    "test_assambly": test_assambly,
                    "test_clas": test_clas,
                    "test_method": test_method,
                }
                
                # Remove None values so they don't get sent as null
                params = {k: v for k, v in params.items() if v is not None}
                
                response = send_command_with_retry("run_play_mode_tests", params)
                
                if not response.get("success"):
                    return response
                
                # Build test description for messages
                if not test_assambly and not test_clas and not test_method:
                    test_description = "all tests"
                elif test_method:
                    test_description = f"Class: {test_clas}, Method: {test_method}"
                elif test_clas:
                    test_description = f"Class: {test_clas}"
                else:
                    test_description = f"Assembly: {test_assambly}"
                    
                # Poll for test to complete
                timeout = 60.0  # 60 second timeout for full test execution
                start_time = time.time()
                last_status = ""
                test_started = False
                
                while time.time() - start_time < timeout:
                    try:
                        # Check workflow status
                        status_response = send_command_with_retry("run_play_mode_tests", {
                            "action": "status"
                        })
                        
                        if status_response.get("success"):
                            data = status_response.get("data", {})
                            workflow_status = data.get("workflow_status", "")
                            
                            # Log status changes for debugging
                            if workflow_status != last_status:
                                logger.debug(f"Workflow status: {workflow_status}")
                                last_status = workflow_status
                            
                            # Track when test actually starts running
                            if workflow_status == "RUNNING_TEST":
                                test_started = True
                                logger.debug(f"Test execution started: {test_description}")
                            
                            # Return when test completes
                            elif workflow_status == "COMPLETED":
                                if test_started:
                                    return {
                                        "success": True, 
                                        "message": f"Test execution completed: {test_description}",
                                        "data": {"workflow_status": workflow_status, "test_executed": True}
                                    }
                                else:
                                    # Test completed but never saw it start (might have been very quick)
                                    return {
                                        "success": True, 
                                        "message": f"Test execution completed: {test_description} (immediate completion)",
                                        "data": {"workflow_status": workflow_status, "test_executed": True}
                                    }
                        
                    except Exception as e:
                        # Connection might be lost during domain reload, continue polling
                        logger.debug(f"Status check failed (expected during domain reload): {e}")
                    
                    time.sleep(0.5)  # Wait 500ms before next check
                
                # Timeout occurred
                if test_started:
                    return {
                        "success": False, 
                        "message": f"Timeout waiting for test to complete: {test_description} (test was running)"
                    }
                else:
                    return {
                        "success": False, 
                        "message": f"Timeout waiting for test to start: {test_description}"
                    }
            else:
                return {"success": False, "message": f"Unknown action: {action}"}

        except Exception as e:
            # Handle Python-side errors (e.g., connection issues)
            return {"success": False, "message": f"Python error in run_play_mode_tests: {str(e)}"}