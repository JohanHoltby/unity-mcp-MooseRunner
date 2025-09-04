Install all the prerequsits in: https://github.com/JohanHoltby/unity-mcp-MooseRunner/blob/main/README.md
For the git repo instead fork main repo. Unleas you intend to to PR to main repo.
go to root of your git (I asume you use GIT to track your main project)
RUN-->
git submodule add -b main https://github.com/YourUserName/unity-mcp-YourFork.git Packages/unity-mcp-YourFork
# Then in Packages/manifest.json:
#  "com.<exact.name.from.package.json>": "file:Packages/unity-mcp-YourFork/UnityMcpBridge"
# or you can add it using the package manager and point to the file location.
git add Packages/manifest.json .gitmodules Packages/unity-mcp-YourFork
git commit -m "Use UnityMcpBridge via submodule"

Unity MCP is now installed in your project and is easy to edit.

Update UpdateInstruction.md in MCPAddTool and the files which are copied.

then folow the instruction or ask ai to do it.

To test the python side find the AppData folder e.g. C:\Users\UserName\AppData\Local\UnityMCP and remove it. Next time unity start it will be installed again.
you can test start the server using "uv run server.py 2>&1" and then see any errors.

	
	
	

