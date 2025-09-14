using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using UnityEngine;
using MCPForUnity.Editor.Helpers; // For Response class
using MooseRunner.Editor.API;

namespace MCPForUnity.Editor.Tools
{
    /// <summary>
    /// Handles executing Unity Editor menu items by path.
    /// </summary>
    public static class RunPlayModeTests
    {

        /// <summary>
        /// Main handler for executing menu items or getting available ones.
        /// </summary>
        public static object HandleCommand(JObject @params)
        {
            string action = @params["action"]?.ToString().ToLower() ?? "run"; // Default action

            try
            {
                switch (action)
                {
                    case "run":
                        return RunTest(@params);
                    case "status":
                        // Get workflow status with error information
                        var statusInfo = MooseRunnerAPI.Instance.GetWorkflowStatusWithError();
                        
                        // Prepare the response data - use object type to allow different values
                        object responseData;
                        
                        // If workflow is completed, include test results
                        if (statusInfo.status == "COMPLETED")
                        {
                            var testResult = MooseRunnerAPI.Instance.GetTestExecutionResult();
                            var testSummary = MooseRunnerAPI.Instance.GetTestExecutionSummary();
                            
                            responseData = new {
                                workflow_status = statusInfo.status,
                                error_message = statusInfo.error,
                                is_playing = UnityEditor.EditorApplication.isPlaying,
                                is_compiling = UnityEditor.EditorApplication.isCompiling,
                                test_result = testResult.ToString(),
                                test_summary = new {
                                    status = testSummary.status.ToString(),
                                    total = testSummary.total,
                                    passed = testSummary.passed,
                                    failed = testSummary.failed,
                                    not_run = testSummary.notRun
                                }
                            };
                        }
                        else
                        {
                            responseData = new {
                                workflow_status = statusInfo.status,
                                error_message = statusInfo.error,
                                is_playing = UnityEditor.EditorApplication.isPlaying,
                                is_compiling = UnityEditor.EditorApplication.isCompiling,
                                test_result = (string)null,
                                test_summary = (object)null
                            };
                        }
                        
                        return Response.Success("Workflow status retrieved", responseData);
                    default:
                        return Response.Error(
                            $"Unknown action: '{action}'. Valid actions are 'execute', 'get_available_menus'."
                        );
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[RunPlayModeTests] Action '{action}' failed: {e}");
                return Response.Error($"Internal error processing action '{action}': {e.Message}");
            }
        }

        /// <summary>
        /// Run a play mode test
        /// </summary>
        private static object RunTest(JObject @params)
        {
            // Note: MooseRunnerAPI.RunTest uses StartManagedTestExecution which handles
            // compilation waiting and play mode transitions automatically.
            // We don't need to check play mode here.

            // Try both naming conventions: snake_case and camelCase
            string test_assembly = @params["test_assembly"]?.ToString();
            string test_class = @params["test_class"]?.ToString();
            string test_method = @params["test_method"]?.ToString();

            try
            {
                // Validate that at least one test parameter is specified
                if (string.IsNullOrEmpty(test_assembly) &&
                    string.IsNullOrEmpty(test_class) &&
                    string.IsNullOrEmpty(test_method))
                {
                    return Response.Error(
                        "At least one of test_assembly, test_class, or test_method must be specified. Running all tests is not supported via MCP."
                    );
                }

                // Never run all tests via MCP - always specify a scope
                bool rootSelected = false;

                // Call the MooseRunnerAPI which now handles all validation and thread safety internally
                // The API will throw exceptions for invalid parameters, which we catch and return as errors
                MooseRunnerAPI.Instance.RunTest(rootSelected, test_assembly, test_class, test_method);
                
                // Build description of what's being run
                string testDescription;
                if (!string.IsNullOrEmpty(test_method))
                {
                    testDescription = $"Class: {test_class}, Method: {test_method}";
                }
                else if (!string.IsNullOrEmpty(test_class))
                {
                    testDescription = $"Class: {test_class}";
                }
                else
                {
                    testDescription = $"Assembly: {test_assembly}";
                }
                    
                return Response.Success(
                    $"Test execution scheduled: {testDescription}. Check Unity logs for results."
                );
            }
            catch (ArgumentException argEx)
            {
                // Parameter validation errors from MooseRunnerAPI
                return Response.Error(argEx.Message);
            }
            catch (Exception e)
            {
                // Unexpected errors
                Debug.LogError($"[RunPlayModeTests] Unexpected error: {e}");
                return Response.Error($"Unexpected error: {e.Message}");
            }
        }

        // TODO: Add helper for alias lookup if implementing aliases.
        // private static string LookupAlias(string alias) { ... return actualMenuPath or null ... }
    }
}

