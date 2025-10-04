"""
Defines the run_play_mode_tests tool for running Unity play mode tests.
"""
import asyncio
from typing import Annotated, Any, Literal
import time
import logging

from mcp.server.fastmcp import Context
from registry import mcp_for_unity_tool
from unity_connection import async_send_command_with_retry

logger = logging.getLogger("mcp-for-unity-server")


@mcp_for_unity_tool(
    description="Run play mode tests.\n\nRunning all tests in the project is not supported via MCP.\n\nMethod requires: test_assembly, test_class, and test_method.\nClass requires: test_assembly and test_class.\nAssembly requires: test_assembly only.\n\nArgs:\n    action: Operation ('run_test_method', 'run_test_class', 'run_test_asmdef').\n    test_assembly: The assembly name (required for all actions).\n    test_class: The class name (required for run_test_method and run_test_class).\n    test_method: The method name (required for run_test_method only).\n    timeout: Maximum time in seconds to wait for test completion (default: 360, max: 600).\n\nReturns:\n    Dictionary with results ('success', 'message', 'data').\n"
)
async def run_play_mode_tests(
    ctx: Context,
    action: Annotated[str, "Operation ('run_test_method', 'run_test_class', 'run_test_asmdef')"],
    test_assembly: Annotated[str, "The assembly name (required for all actions)"],
    test_class: Annotated[str, "The class name (required for run_test_method and run_test_class)"],
    test_method: Annotated[str, "The method name (required for run_test_method only)"],
    timeout: Annotated[int, "Maximum time in seconds to wait for test completion (default: 360, max: 600)"] = 360,
) -> dict[str, Any]:
    """Run play mode tests."""
    ctx.info(f"Processing run_play_mode_tests: {action}")
    try:
        if action == "run_test_method" or action == "run_test_class" or action == "run_test_asmdef":
            # Action-specific parameter validation
            if action == "run_test_method":
                # Method requires assembly, class and method names
                if not test_assembly or not test_class or not test_method:
                    return {
                        "success": False,
                        "message": "run_test_method requires test_assembly, test_class and test_method parameters."
                    }

            elif action == "run_test_class":
                # Class requires assembly and class name, method must not be provided
                if not test_assembly or not test_class:
                    return {
                        "success": False,
                        "message": "run_test_class requires test_assembly and test_class parameters. test_method must not be provided."
                    }
                if test_method:
                    return {
                        "success": False,
                        "message": "run_test_class cannot have test_method parameter. Use run_test_method for specific method testing."
                    }

            elif action == "run_test_asmdef":
                # Assembly requires assembly name, class and method must not be provided
                if not test_assembly:
                    return {
                        "success": False,
                        "message": "run_test_asmdef requires test_assembly parameter. test_class and test_method must not be provided."
                    }
                if test_class or test_method:
                    return {
                        "success": False,
                        "message": "run_test_asmdef cannot have test_class or test_method parameters. Use run_test_class or run_test_method for more specific testing."
                    }

            # Build params based on action type (MooseRunner hierarchy requirement)
            if action == "run_test_method":
                # Only pass method parameter to Unity (class needed for lookup but cleared for Unity)
                params = {
                    "action": action,
                    "test_assembly": test_assembly,
                    "test_class": test_class,
                    "test_method": test_method,
                }
            elif action == "run_test_class":
                # Only pass class parameter to Unity
                params = {
                    "action": action,
                    "test_assembly": test_assembly,
                    "test_class": test_class,
                    "test_method": "",
                }
            elif action == "run_test_asmdef":
                # Only pass assembly parameter to Unity
                params = {
                    "action": action,
                    "test_assembly": test_assembly,
                    "test_class": "",
                    "test_method": "",
                }

            # Get the current asyncio event loop
            loop = asyncio.get_running_loop()

            response = await async_send_command_with_retry("run_play_mode_tests", params, loop=loop)

            if not response.get("success"):
                return response

            # Build test description for messages
            if action == "run_test_method":
                test_description = f"Assembly: {test_assembly}, Class: {test_class}, Method: {test_method}"
            elif action == "run_test_class":
                test_description = f"Assembly: {test_assembly}, Class: {test_class}"
            else:  # run_test_asmdef
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
                    status_response = await async_send_command_with_retry("run_play_mode_tests", {
                        "action": "status"
                    }, loop=loop)

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

                await asyncio.sleep(0.5)  # Wait 500ms before next check

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
