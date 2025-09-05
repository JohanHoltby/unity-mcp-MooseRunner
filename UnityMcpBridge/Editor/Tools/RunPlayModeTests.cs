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
                        // Return current workflow status
                        string workflowStatus = MooseRunnerAPI.Instance.GetWorkflowStatus();
                        return Response.Success("Workflow status retrieved", new {
                            workflow_status = workflowStatus,
                            is_playing = UnityEditor.EditorApplication.isPlaying,
                            is_compiling = UnityEditor.EditorApplication.isCompiling
                        });
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
            string test_assembly = @params["test_assembly"]?.ToString() ?? @params["test_assambly"]?.ToString();
            string test_class = @params["test_class"]?.ToString() ?? @params["test_clas"]?.ToString();
            string test_method = @params["test_method"]?.ToString();
            
            try
            {
                // Determine if running all tests
                bool rootSelected = string.IsNullOrEmpty(test_assembly) && 
                                   string.IsNullOrEmpty(test_class) && 
                                   string.IsNullOrEmpty(test_method);
                
                // When running a specific method, don't pass the assembly (per MooseRunner API requirements)
                string assemblyToPass = null;
                if (!string.IsNullOrEmpty(test_method))
                {
                    // Method selection should not include assembly
                    assemblyToPass = null;
                }
                else if (!string.IsNullOrEmpty(test_class))
                {
                    // Class selection should not include assembly  
                    assemblyToPass = null;
                }
                else if (!string.IsNullOrEmpty(test_assembly))
                {
                    // Only assembly selection includes the assembly
                    assemblyToPass = test_assembly;
                }
                
                // Call the MooseRunnerAPI which now handles all validation and thread safety internally
                // The API will throw exceptions for invalid parameters, which we catch and return as errors
                MooseRunnerAPI.Instance.RunTest(rootSelected, assemblyToPass, test_class, test_method);
                
                // Build description of what's being run
                string testDescription;
                if (rootSelected)
                {
                    testDescription = "all tests";
                }
                else if (!string.IsNullOrEmpty(test_method))
                {
                    testDescription = $"Class: {test_class}, Method: {test_method}";
                }
                else if (!string.IsNullOrEmpty(test_class))
                {
                    testDescription = $"Class: {test_class}";
                }
                else
                {
                    testDescription = $"Assembly: {assemblyToPass}";
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

