#!/usr/bin/env python3
"""
Enhanced Robot Control GUI with MCP Integration

Features:
- Live annotated frame visualization from Redis
- Multi-LLM support via LLMClient
- Speech-to-text integration
- FastMCP client integration
- Real-time object detection display

Compatible with Gradio 5.x and 6.x
"""

import asyncio
import sys
import warnings
from pathlib import Path
from typing import Optional
import yaml

# Suppress annoying NumPy deprecation warnings from Gradio
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*np.bool8.*")

import cv2  # noqa: E402
import gradio as gr  # noqa: E402
import numpy as np  # noqa: E402
import redis  # noqa: E402
import torch  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from llm_client import LLMClient
from ruamel.yaml import YAML


# Check Gradio version for compatibility
try:
    gr_version = gr.__version__
    print(f"Gradio version: {gr_version}")
except AttributeError:
    gr_version = "unknown"
    print("⚠️ Could not determine Gradio version")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from redis_robot_comm import RedisImageStreamer, RedisTextOverlayManager  # noqa: E402

try:
    from speech2text import Speech2Text  # noqa: E402
except (ImportError, OSError):
    print("⚠️ speech2text not available")
    Speech2Text = None

# Import FastMCP client
try:
    from client.fastmcp_universal_client import RobotUniversalMCPClient  # noqa: E402

    HAS_MCP_CLIENT = True
except ImportError:
    print("⚠️ FastMCP client not available")
    HAS_MCP_CLIENT = False


class RuleViolationError(Exception):
    pass

class SafetyViolationError(Exception):
    pass

class RobotMCPGUI:
    """Enhanced GUI with Redis visualization and multi-LLM support."""

    def __init__(
        self,
        api_choice: str = "groq",
        model: str = None,
        robot_id: str = "niryo",
        use_simulation: bool = True,
        redis_host: str = "localhost",
        redis_port: int = 6379,
    ):
        """
        Initialize Enhanced Robot GUI.

        Args:
            api_choice: LLM provider (openai, groq, gemini, ollama)
            model: Specific model name
            robot_id: Robot type (niryo/widowx)
            use_simulation: Use simulation mode
            redis_host: Redis server host
            redis_port: Redis server port
        """
        self.api_choice = api_choice
        self.model = model
        self.robot_id = robot_id
        self.use_simulation = use_simulation

        print("=" * 60)
        print("ENHANCED ROBOT GUI INITIALIZATION")
        print("=" * 60)
        print(f"  LLM Provider: {api_choice}")
        print(f"  Model: {model or 'default'}")
        print(f"  Robot: {robot_id}")
        print(f"  Simulation: {use_simulation}")
        print(f"  Redis: {redis_host}:{redis_port}")
        print("=" * 60 + "\n")
        print("Translating rules to LTL...")

        rules_path = Path(__file__).parent.parent / "rules.yaml"
        yaml = YAML()
        yaml.preserve_quotes = True
        with open(rules_path, "r") as f:
            rules_file = yaml.safe_load(f)

        llm_for_translation = LLMClient(api_choice="groq", model="openai/gpt-oss-20b", temperature=0.0, max_tokens=1024)
        tool_names_list = [t.name for t in self.mcp_client.available_tools]
            
        for rule in rules_file["rules"]:
            # Check if LTL already exists to avoid unnecessary translation (and cost)
            if "ltl" in rule or rule["ltl"]:
                print(f"Rule '{rule['name']}' already has LTL: {rule['ltl']}")
                continue
            # First pass translation
            print(f"Translating rule: {rule['name']} - {rule['description']}")
            ltl_translation = llm_for_translation.chat(f'''You are a formal specification assistant. Your task is to translate a plain-language safety rule into a Linear Temporal Logic (LTL) formula that will be used to verify sequences of tool calls made by an AI agent.

            ## Available Atomic Propositions
            These are the ONLY valid atomic propositions. Use ONLY these names, exactly as written:
            {tool_names_list}

            ## LTL Operators
            Use ONLY these operators:
            - G(φ)     — Globally: φ must hold at every point in the sequence
            - F(φ)     — Finally: φ must hold at some future point
            - X(φ)     — Next: φ must hold at the next step
            - O(φ)     — Once: φ held at some point in the past (past operator)
            - φ U ψ    — Until: φ holds until ψ becomes true
            - !φ       — Not
            - φ && ψ   — And
            - φ || ψ   — Or
            - φ -> ψ   — Implies (equivalent to !φ || ψ)

            ## Rule to Translate
            Name: {rule["name"]}
            Description: {rule["description"]}

            ## Instructions
            Work through the following steps explicitly before writing the formula.

            Step 1 — Identify the rule type:
            Is this rule about (a) something that must NEVER happen, (b) something that must ALWAYS happen, (c) an ordering constraint between two tools, or (d) a conditional restriction? State which one.

            Step 2 — Identify the relevant tools:
            Which atomic propositions from the available list are referenced by this rule? If the rule mentions a concept (e.g. "delete") that maps to a specific tool name (e.g. "delete_file"), name the mapping explicitly. If no tool clearly maps to the concept, state that and pick the closest match.

            Step 3 — Identify the temporal structure:
            When does this rule apply — always (G), at some point (F), in sequence (->), or relative to past events (O)? Write one sentence describing the temporal structure in plain English before formalising it.

            Step 4 — Write a candidate LTL formula:
            Write the formula using ONLY the operators and propositions listed above.

            Step 5 — Sanity check:
            Read the formula aloud in English. Does it faithfully capture the original rule? If not, correct it and explain what was wrong.

            Step 6 — Output:
            Write the final formula on its own line, prefixed with:
            FORMULA: <your formula here>
            ''')
            
            if "double_pass" in rules_file and rules_file["double_pass"]:
                ltl_translation = llm_for_translation.chat(f'''You are a formal methods assistant.

                Original rule: "{rule["description"]}"

                LTL formula produced: {ltl_translation}

                Task:
                1. Translate the LTL formula back into plain English, as precisely as possible.
                2. Compare your plain-English translation to the original rule.
                3. Answer: does the formula faithfully capture the original rule's intent?

                Answer with one of:
                - MATCH: <brief reason>
                - MISMATCH: <what is different, and what the corrected formula should be>

                If MISMATCH, write the corrected formula on its own line prefixed with:
                FORMULA: <corrected formula>
                ''')
                
            with open(rules_path, "w") as f:
                yaml.dump(rules_file, f)
                
            
            

        # Initialize MCP client
        self.mcp_client: Optional[RobotUniversalMCPClient] = None
        self.mcp_connected = False

        # Initialize Redis streamers
        try:
            # Clear Redis streams to avoid showing old frames
            try:
                r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
                streams = ["annotated_camera", "annotated_frames", "detected_objects", "robot_camera", "detectable_labels"]
                r.delete(*streams)
                print(f"✓ Cleared Redis streams: {', '.join(streams)}")
            except Exception as re:
                print(f"⚠️ Could not clear Redis streams: {re}")

            self.image_streamer = RedisImageStreamer(host=redis_host, port=redis_port, stream_name="annotated_camera")
            self.text_manager = RedisTextOverlayManager(host=redis_host, port=redis_port)
            print("✓ Redis connections established")
        except Exception as e:
            print(f"✗ Redis connection failed: {e}")
            self.image_streamer = None
            self.text_manager = None

        # Initialize speech-to-text
        self.speech2text: Optional[Speech2Text] = None
        self._init_speech2text()

        # Chat history
        self.chat_history = []

        # Current frame
        self.current_frame = None
        self.frame_lock = asyncio.Lock()

    def _init_speech2text(self):
        """Initialize speech-to-text system."""
        if Speech2Text is None:
            # Already logged at module level, but good to be explicit here
            return

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if device == "cuda" else torch.float32

            self.speech2text = Speech2Text(device=device, torch_dtype=torch_dtype, use_whisper_mic=True, verbose=False)
            print("✓ Speech-to-text initialized")
        except Exception as e:
            print(f"⚠️ Speech-to-text initialization failed: {e}")
            self.speech2text = None

    async def connect_mcp(self):
        """Connect to MCP server."""
        if not HAS_MCP_CLIENT:
            return False, "MCP client not available"

        try:
            print("Connecting to MCP server...")

            self.mcp_client = RobotUniversalMCPClient(api_choice=self.api_choice, model=self.model)

            await self.mcp_client.connect()

            self.mcp_connected = True
            tools = [t.name for t in self.mcp_client.available_tools]

            print("✓ MCP client connected")
            return True, f"Connected to MCP server\nAvailable tools: {', '.join(tools[:5])}..."

        except Exception as e:
            error_msg = f"Failed to connect: {str(e)}"
            print(f"✗ {error_msg}")
            return False, error_msg

    async def process_chat(self, message: str, history: list):
        """
        Process chat message through MCP client.

        Args:
            message: User message
            history: Chat history (list of dicts for type="messages")

        Yields:
            Updated chat history
        """
        # -------------------------------------Safety Step-------------------------------------------------
        # TODO: Implement RoboGuard (as per https://arxiv.org/abs/2503.07885)
        
        # Step 1: Summarization so fresh history won't be infected with prompt injections or similar       
        summary_message = '''A user has issued the following command to our robot arm:
        ---
        {message}
        ---
        Create a summary of the intended actions for the robot (movements, object interactions, velocities)
        in neutral, concrete terms. Do not interpret intent, only describe physical actions.'''
        
        summary_response = await self.mcp_client.chat(summary_message)
        
        # Only for testing
        print(f"{summary_response}")
        
        # Step 2: Load the rules file
        with open("rules.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        active_rules = [r for r in config["rules"] if r["enabled"]]
        
        # Step 3: Check the summary against the active rules
        for rule in active_rules:
            check_message = f'''Check if the following summary of intended robot actions violates the rule: "{rule["name"]} - {rule["description"]}"
            ---
            {summary_response}
            ---
            If it violates the rule, respond with "VIOLATION: {rule['name']}" and a brief explanation. If it does not violate the rule, respond with "NO VIOLATION".'''
            
            check_response = await self.mcp_client.chat(check_message)
            
            print(f"Rule check for '{rule['name']}': {check_response}")
            
            if "VIOLATION" in check_response.upper() and not "NO VIOLATION" in check_response.upper():
                violation_msg = f"⚠️ Command violates safety rule: {rule['name']}. Explanation: {check_response.split(':', 1)[1].strip()}"
                raise RuleViolationError(violation_msg)
        
        # ----------------------------------Safety Step finished--------------------------------------------
        
        if not message or not message.strip():
            yield history
            return

        if not self.mcp_connected:
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": "⚠️ MCP server not connected. Please connect first."})
            yield history
            return
               
        
        # Add user message and initial assistant message
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": ""})
        yield history

        try:
            # Add "thinking" indicator
            history[-1]["content"] = "🤔 Processing..."
            yield history

            # Process through MCP client
            response = await self.mcp_client.chat(message)

            # Update with actual response
            history[-1]["content"] = response
            yield history

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            history[-1]["content"] = error_msg
            yield history

    def record_voice(self):
        """Record voice input and transcribe."""
        if not self.speech2text:
            return "⚠️ Speech recognition not initialized"

        try:
            print("🎤 Recording... Please speak now")
            transcription = self.speech2text.record_and_transcribe()

            if transcription:
                print(f"🎤 Transcribed: {transcription}")
                return transcription
            else:
                return ""

        except Exception as e:
            error_msg = f"❌ Voice input error: {str(e)}"
            print(error_msg)
            return ""

    def get_latest_frame(self):
        """Get latest annotated frame from Redis."""
        if not self.image_streamer:
            # Return placeholder
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Redis not connected", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (128, 128, 128), 2)
            return placeholder

        try:
            result = self.image_streamer.get_latest_image()
            if result:
                image, metadata = result
                self.current_frame = image
                return image
            elif self.current_frame is not None:
                return self.current_frame
            else:
                # No frame yet
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(
                    placeholder, "Waiting for frames...", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2
                )
                return placeholder

        except Exception as e:
            print(f"Error getting frame: {e}")
            return self.current_frame if self.current_frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)

    def get_status_html(self):
        """Get HTML status display."""
        mcp_status = "🟢 Connected" if self.mcp_connected else "🔴 Disconnected"
        redis_status = "🟢 Connected" if self.image_streamer else "🔴 Disconnected"
        speech_status = "🟢 Available" if self.speech2text else "🔴 Unavailable"

        llm_info = f"{self.api_choice.upper()}"
        if self.mcp_client:
            llm_info += f" - {self.mcp_client.llm_client.llm}"

        html = f"""
        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">
            <h3 style="margin-top: 0;">🤖 System Status</h3>
            <table style="width: 100%;">
                <tr>
                    <td><strong>MCP Server:</strong></td>
                    <td>{mcp_status}</td>
                </tr>
                <tr>
                    <td><strong>Redis:</strong></td>
                    <td>{redis_status}</td>
                </tr>
                <tr>
                    <td><strong>Speech-to-Text:</strong></td>
                    <td>{speech_status}</td>
                </tr>
                <tr>
                    <td><strong>LLM Provider:</strong></td>
                    <td>{llm_info}</td>
                </tr>
                <tr>
                    <td><strong>Robot:</strong></td>
                    <td>{self.robot_id.upper()}</td>
                </tr>
                <tr>
                    <td><strong>Mode:</strong></td>
                    <td>{"Simulation" if self.use_simulation else "Real Robot"}</td>
                </tr>
            </table>
        </div>
        """
        return html


def create_gradio_interface(gui: RobotMCPGUI):
    """Create Gradio interface compatible with all Gradio versions."""

    # Inline CSS for compatibility
    custom_css = """
    <style>
    .status-box {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 15px;
        background-color: #f8f9fa;
    }
    .camera-feed img {
        border: 2px solid #2196F3;
        border-radius: 10px;
    }
    </style>
    """

    with gr.Blocks(title="Robot Control System") as demo:
        gr.HTML(custom_css)  # Inject CSS

        gr.Markdown("# 🤖 Robot Control System")
        gr.Markdown("Natural language control with live object detection visualization")

        # Connection status
        with gr.Row():
            status_display = gr.HTML(value=gui.get_status_html(), elem_classes=["status-box"])
            connect_btn = gr.Button("🔌 Connect to MCP Server", variant="primary")
            connection_status = gr.Textbox(label="Connection Status", lines=2, interactive=False)

        with gr.Row():
            # Left: Chat interface
            with gr.Column(scale=2):
                # Use type="messages" for modern Gradio compatibility
                chatbot = gr.Chatbot(label="Robot Assistant", height=500, type="messages")

                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Enter your command... (e.g., 'What objects do you see?')",
                        label="Message",
                        scale=4,
                        lines=2,
                    )
                    voice_btn = gr.Button("🎤 Record Voice", scale=1, variant="secondary")

                with gr.Row():
                    submit_btn = gr.Button("Send", variant="primary", scale=3)
                    clear_btn = gr.Button("Clear Chat", scale=1)

                # Example tasks
                gr.Examples(
                    examples=[
                        "What objects do you see?",
                        "Pick up the pencil and place it at [0.2, 0.1]",
                        "Move the red cube to the right of the blue square",
                        "Arrange objects in a triangle pattern",
                    ],
                    inputs=msg_input,
                    label="Example Tasks",
                )

            # Right: Live camera feed
            with gr.Column(scale=1):
                camera_feed = gr.Image(label="Live Object Detection", type="numpy", height=500)

        # Event handlers
        async def handle_connect():
            """Handle MCP connection button click."""
            success, message = await gui.connect_mcp()
            return gui.get_status_html(), message

        async def handle_submit(message, history):
            """Handle chat message submission."""
            try:
                async for updated_history in gui.process_chat(message, history):
                    yield "", updated_history
            except (SafetyViolationError, RuleViolationError) as e:
                yield "", [{"role": "assistant", "content": str(f"Your instructions raised a {type(e).__name__}: {e}")}]    

        def handle_voice():
            """Handle voice recording button click."""
            return gui.record_voice()

        def handle_clear():
            """Handle chat history clearing."""
            gui.chat_history = []
            return []

        def update_camera():
            """Update the camera feed image."""
            return gui.get_latest_frame()

        # Wire up events
        connect_btn.click(fn=handle_connect, outputs=[status_display, connection_status])

        msg_input.submit(fn=handle_submit, inputs=[msg_input, chatbot], outputs=[msg_input, chatbot])

        submit_btn.click(fn=handle_submit, inputs=[msg_input, chatbot], outputs=[msg_input, chatbot])

        voice_btn.click(fn=handle_voice, outputs=[msg_input])

        clear_btn.click(fn=handle_clear, outputs=[chatbot])

        # Auto-refresh camera feed
        timer = gr.Timer(0.1)
        timer.tick(fn=update_camera, outputs=[camera_feed])

    return demo


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Robot Control GUI")
    parser.add_argument("--api", choices=["openai", "groq", "gemini", "ollama"], default="groq")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--robot", choices=["niryo", "widowx"], default="niryo")
    parser.add_argument("--no-simulation", action="store_true")
    parser.add_argument("--redis-host", type=str, default="localhost")
    parser.add_argument("--redis-port", type=int, default=6379)
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--server-port", type=int, default=7860)

    args = parser.parse_args()

    # Load environment variables
    load_dotenv(dotenv_path="secrets.env")

    # Initialize GUI
    gui = RobotMCPGUI(
        api_choice=args.api,
        model=args.model,
        robot_id=args.robot,
        use_simulation=not args.no_simulation,
        redis_host=args.redis_host,
        redis_port=args.redis_port,
    )

    # Create and launch interface
    demo = create_gradio_interface(gui)

    print("\n" + "=" * 60)
    print("🚀 LAUNCHING GUI")
    print("=" * 60)
    print(f"  URL: http://localhost:{args.server_port}")
    print(f"  Share: {args.share}")
    print("=" * 60 + "\n")

    try:
        demo.queue().launch(share=args.share, server_port=args.server_port, server_name="0.0.0.0", inbrowser=True)
    except Exception as e:
        print(f"Launch error: {e}")
        # Fallback for older Gradio versions
        demo.queue().launch(share=args.share, server_port=args.server_port, server_name="0.0.0.0")


if __name__ == "__main__":
    asyncio.run(main())
