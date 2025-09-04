using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using UnityEngine;
using MCPForUnity.Editor.Helpers; // For Response class
using MooseRunner.Editor.API;

namespace MCPForUnity.Editor.Tools
{
    /// <summary>
    /// Handles some thing your tool do
    /// </summary>
    public static class YourTool
    {

        /// <summary>
        /// Main handler for executing your tool
        /// </summary>
        public static object HandleCommand(JObject @params)
        {
            string action = @params["action"]?.ToString().ToLower() ?? "run"; // Default action

            try
            {
                switch (action)
                {
                    case "action1":
                        return Action1(@params);
                    case "Action2":
						return Action2(@params);
                    default:
                        return Response.Error(
                            $"Unknown action: '{action}'. Valid actions are 'action1', 'action2'."
                        );
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[YourTool] Action '{action}' failed: {e}");
                return Response.Error($"Internal error processing action '{action}': {e.Message}");
            }
        }

        /// <summary>
        /// description of your tool
        /// </summary>
        private static object Action1(JObject @params)
        {
			try{
                YourAction1ImplementedSomeWhereElse();
				
                return Response.Success(
                    "’Action1’ was completed with sucsess."
                );
            }
            catch (ArgumentException argEx)
            {
                return Response.Error(argEx.Message);
            }
            catch (Exception e)
            {
                // Unexpected errors
                Debug.LogError($"[YourTool] Unexpected error: {e}");
                return Response.Error($"Unexpected error: {e.Message}");
            }
        }

	     /// <summary>
        /// description of your tool
        /// </summary>
        private static object Action2(JObject @params)
        {
			try{
                YourAction2ImplementedSomeWhereElse();
				
                return Response.Success(
                    "’Action2’ was completed with sucsess."
                );
            }
            catch (ArgumentException argEx)
            {
                return Response.Error(argEx.Message);
            }
            catch (Exception e)
            {
                // Unexpected errors
                Debug.LogError($"[YourTool] Unexpected error: {e}");
                return Response.Error($"Unexpected error: {e.Message}");
            }
        }

        // TODO: Add helper for alias lookup if implementing aliases.
        // private static string LookupAlias(string alias) { ... return actualMenuPath or null ... }
    }
}

