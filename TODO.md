# ToDos:
[Check the transcribed Speech to Text for any unsafe words/sentiments (mcp_app.py line 192)](./robot_gui/mcp_app.py#L192)?
    - implement word blacklist (i.e. "human", "person", "outside"?)
- Have transcript checked by LLM for harmful instructions, aka second pass (not very effective)
    - Implement RoboGuard-style two stage check so LLM does not see user input in that call

- implement settings file
- implement loading settings file
- implement checks for settings