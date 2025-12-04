from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from tools import available_tools, handle_tool_call

# Load environment variables from .env file (for local development)
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORT = int(os.getenv('PORT', 3000))

# Initialize Anthropic client
anthropic_client = Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY', 'your-api-key-here')
)

# Store messages in memory (simple chat)
messages = []
# Store API-formatted conversation history
conversation = []

# Mount static files
app.mount("/static", StaticFiles(directory="public"), name="static")

class MessageRequest(BaseModel):
    username: str
    message: str

class MessageResponse(BaseModel):
    id: int
    username: str
    message: str
    timestamp: str

@app.get("/")
async def serve_index():
    return FileResponse('public/index.html')

@app.get("/style.css")
async def serve_css():
    return FileResponse('public/style.css')

@app.get("/script.js")
async def serve_js():
    return FileResponse('public/script.js')

@app.get("/messages")
async def get_messages():
    return messages

@app.post("/messages")
async def post_message(request: MessageRequest):
    if not request.username or not request.message:
        raise HTTPException(status_code=400, detail="Username and message required")
    
    user_message = {
        'id': int(time.time() * 1000),
        'username': request.username,
        'message': request.message,
        'timestamp': datetime.now().isoformat()
    }
    
    messages.append(user_message)
    conversation.append({"role": "user", "content": request.message})
    print('New message:', user_message)
    
    # Get AI response from Claude using the conversation history
    try:
        print("Waiting for response...")
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=conversation,
            tools=available_tools
        )
        print("...")
        print("...")
        print("entire response")
        print(response)
        
        # Check if response contains tool calls
        has_tool_use = any(content.type == "tool_use" for content in response.content)
        
        if has_tool_use:
            print("Tool use detected!")
            
            # Add the assistant's response to conversation
            conversation.append({"role": "assistant", "content": response.content})
            
            # Handle each tool call
            tool_results = []
            for content in response.content:
                if content.type == "tool_use":
                    print(f"Calling tool: {content.name}")
                    tool_result = handle_tool_call(content.name, content.input)
                    print(f"Tool result: {tool_result}")
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": str(tool_result)
                    })
            
            # Add tool results to conversation
            conversation.append({"role": "user", "content": tool_results})
            
            # Get final response after tool use
            print("Getting final response after tool use...")
            final_response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=conversation,
                tools=available_tools
            )
            print(f"Final response: {final_response}")
            
            ai_message = {
                'id': int(time.time() * 1000) + 1,
                'username': 'Claude',
                'message': final_response.content[0].text,
                'timestamp': datetime.now().isoformat()
            }
            conversation.append({"role": "assistant", "content": final_response.content[0].text})
        else:
            # Regular text response
            ai_message = {
                'id': int(time.time() * 1000) + 1,
                'username': 'Claude',
                'message': response.content[0].text,
                'timestamp': datetime.now().isoformat()
            }
            conversation.append({"role": "assistant", "content": response.content[0].text})

        messages.append(ai_message)
        
        print('AI response:', ai_message)
        
    except Exception as error:
        print('AI Error:', error)
        error_message = {
            'id': int(time.time() * 1000) + 1,
            'username': 'Claude',
            'message': "Sorry, I'm having trouble connecting right now. Please check your API key.",
            'timestamp': datetime.now().isoformat()
        }
        messages.append(error_message)
        conversation.append({"role": "assistant", "content": "Sorry, I'm having trouble connecting right now. Please check your API key."})
    
    return user_message

if __name__ == '__main__':
    import uvicorn
    print(f'Server is running on port {PORT}')
    uvicorn.run(app, host='0.0.0.0', port=PORT)