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
        test_assembly: str,
        test_class: str,
        test_method: str,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """Run play mode tests.

        At least one of test_assembly, test_class, or test_method must be specified.
        Running all tests in the project is not supported via MCP.

        Method requires: test_method, test_class and may set test_assembly (if multiple class exist with same name in different assemblies).
        Class require: test_class to be set and may set test_assembly.
        Assembly require: test_assembly to be set.

        Args:
            action: Operation ('run_test_method', 'run_test_class', 'run_test_asmdef').
            test_assembly: The assembly specified if testing an assembly, if not specified first class found in an assembly will be used. (default: "").
            test_class: The class specified NEEDED if a class or method is to be tested (default: "").
            test_method: The method specified. NEEDED if a method is to be tested (default: "").
            timeout: Maximum time in seconds to wait for test completion (default: 120, max: 600).

        Returns:
            Dictionary with results ('success', 'message', 'data').
        """
        try:
            if action == "run_test_method" or action == "run_test_class" or action == "run_test_asmdef":
                # Validate that at least one test parameter is specified
                if not test_assembly and not test_class and not test_method:
                    return {
                        "success": False,
                        "message": "At least one of test_assembly, test_class, or test_method must be specified. Running all tests is not supported via MCP."
                    }

                # Start test execution
                params = {
                    "action": action,
                    "test_assembly": test_assembly,
                    "test_class": test_class,
                    "test_method": test_method,
                }

                # Remove None values so they don't get sent as null
                params = {k: v for k, v in params.items() if v is not None}
                
                response = send_command_with_retry("run_play_mode_tests", params)
                
                if not response.get("success"):
                    return response
                
                # Build test description for messages
                if test_method:
                    test_description = f"Class: {test_class}, Method: {test_method}"
                elif test_class:
                    test_description = f"Class: {test_class}"
                else:
                    test_description = f"Assembly: {test_assembly}"
                    
                # Validate and clamp timeout to reasonable bounds
                timeout = max(1, min(timeout, 600))  # Clamp between 1 and 600 seconds
                
                # Poll for test to complete
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
                            error_message = data.get("error_message", "")
                            
                            # Check for ERROR state first
                            if workflow_status == "ERROR":
                                return {
                                    "success": False,
                                    "message": f"Test execution failed: {error_message}",
                                    "data": {"workflow_status": workflow_status, "error": error_message}
                                }
                            
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
                                # Extract test results if available
                                test_result = data.get("test_result", "Unknown")
                                test_summary = data.get("test_summary", {})
                                
                                # Build detailed message with test results
                                result_message = f"Test execution completed: {test_description}"
                                
                                # Add result status
                                result_message += f" (Result: {test_result}"
                                
                                # Add counts if available
                                if test_summary and test_summary.get("total", -1) >= 0:
                                    result_message += f", Total: {test_summary.get('total', 0)}"
                                    result_message += f", Passed: {test_summary.get('passed', 0)}"
                                    result_message += f", Failed: {test_summary.get('failed', 0)}"
                                    if test_summary.get('not_run', 0) > 0:
                                        result_message += f", Not Run: {test_summary.get('not_run', 0)}"
                                
                                result_message += ")"
                                
                                if test_started:
                                    return {
                                        "success": True, 
                                        "message": result_message,
                                        "data": {
                                            "workflow_status": workflow_status, 
                                            "test_executed": True,
                                            "test_result": test_result,
                                            "test_summary": test_summary
                                        }
                                    }
                                else:
                                    # Test completed but never saw it start (might have been very quick)
                                    return {
                                        "success": True, 
                                        "message": result_message + " (immediate completion)",
                                        "data": {
                                            "workflow_status": workflow_status, 
                                            "test_executed": True,
                                            "test_result": test_result,
                                            "test_summary": test_summary
                                        }
                                    }
                        
                    except Exception as e:
                        # Connection might be lost during domain reload, continue polling
                        logger.debug(f"Status check failed (expected during domain reload): {e}")
                    
                    time.sleep(0.5)  # Wait 500ms before next check
                
                # Timeout occurred
                if test_started:
                    return {
                        "success": False, 
                        "message": f"Timeout ({timeout}s) waiting for test to complete: {test_description} (test was running)"
                    }
                else:
                    return {
                        "success": False, 
                        "message": f"Timeout ({timeout}s) waiting for test to start: {test_description}"
                    }
            else:
                return {"success": False, "message": f"Unknown action: {action}"}

        except Exception as e:
            # Handle Python-side errors (e.g., connection issues)
            return {"success": False, "message": f"Python error in run_play_mode_tests: {str(e)}"}