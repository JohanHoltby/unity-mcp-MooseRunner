This is a instruction to add a MCP tool to Unity MCP.

Update server.py list
@mcp.prompt()
def asset_creation_strategy() -> str:
    """Guide for discovering and using MCP for Unity tools effectively."""
    return (
	
	by adding the folowing line:
		        "- `your_tool`: Description of your tool for AI to know.\\n\\n"
				
				
Update __init__.py import and mcp init:
at the end of imports add (must map to the your_tool_python.py
from .your_tool_python import register_your_tool_tools

also add this to the same file just above     # Expose resource wrappers as normal. . .
    register_your_tool_tools(mcp)
	

copy the file your_tool_python.py to the \UnityMcpBridge\UnityMcpServer~\src\tools

Now update MCPForUnityBridge.cs under:
// Route command based on the new tool structure from the refactor plan
                object result = command.type switch
                {
				
add the folowing line:
                    "your_tool" => RunPlayModeTests.HandleCommand(paramsObject),

note that ”your_tool” here must map to ”response = send_command_with_retry("your_tool", params)” in your_tool_python.py

copy the file YourTool.cs to the folder UnityMcpBridge\Editor\Tools

update MCPForUnity.Editor.asmdef so the references include any assembly needed for your tool.