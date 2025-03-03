import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, Response
import debugpy
import json
from system_prompt import SYSTEM_MESSAGE  # SYSTEM_MESSAGE is a dictionary
from AgentWrapper import AgentWrapper
from prompt_template import PROMPT_TEMPLATE
from typing import AsyncGenerator
import asyncio
import time
from fastapi.responses import JSONResponse
import logging


logging.basicConfig(level=logging.INFO)


app = FastAPI()
debugpy.listen(("0.0.0.0", 8888))


@app.post("/completion")
async def completion(request: Request):
    """Process GitHub Copilot request and send streamed response."""

    logging.info("✅ GitHub Copilot connected: Processing request...")

    # ✅ Extract request data
    req = await request.json()
    auth_token = request.headers.get("x-github-token")
    messages = req.get("messages", [])

    # ✅ Validate request
    if not auth_token:
        logging.error("❌ Missing authentication token.")
        raise HTTPException(status_code=401, detail="Missing authentication token")

    if not messages:
        logging.error("❌ No messages provided.")
        raise HTTPException(status_code=400, detail="No messages provided")

    latest_message = messages[-1]
    logging.info(f"✅ Successfully received messages: {latest_message['content'][:50]}...")

    # ✅ Start streaming immediately
    async def stream_response():
        yield b"data: {\"choices\":[{\"index\":0,\"delta\":{\"content\":\"Processing...\"}}]}\n\n"  # ✅ Immediate response
        await asyncio.sleep(0.05)

        # ✅ Call the DigitalOcean Product Documentation Agent asynchronously
        agent_response = await product_documentation_agent(latest_message)

        # ✅ Split response into words instead of fixed characters
        def chunk_text(text):
            words = text.split()  # ✅ Split by words to avoid bad substrings
            return words if words else [text]  # ✅ Ensure empty response doesn't break streaming

        response_chunks = chunk_text(agent_response)

        # ✅ Stream response to prevent GitHub timeout
        for chunk in response_chunks:
            if chunk.strip():
                msg = {"choices": [{"index": 0, "delta": {"content": chunk + " "}}]}  # ✅ Add space to avoid merging words
                json_chunk = f"data: {json.dumps(msg, separators=(',', ':'))}\n\n".encode("utf-8")
                logging.info(f"📤 Streaming chunk: {json_chunk.decode('utf-8')}")
                yield json_chunk
                await asyncio.sleep(0.05)

        # ✅ Keep-alive message before stopping
        yield b"data: {\"choices\":[{\"index\":0,\"delta\":{\"content\":\" \"}}]}\n\n"
        await asyncio.sleep(0.1)

        # ✅ Send final stop message
        final_chunk = b"data: {\"choices\":[{\"index\":0,\"delta\":{\"content\":null},\"finish_reason\":\"stop\"}]}\n\n"
        yield final_chunk
        await asyncio.sleep(0.05)

        # ✅ Properly terminate stream
        done_chunk = b"data: [DONE]\n\n"
        logging.info(f"📤 Streaming final termination: {done_chunk.decode('utf-8')}")
        yield done_chunk

    return StreamingResponse(
        stream_response(), 
        media_type="text/event-stream", 
        status_code=200, 
        headers={
            "Connection": "keep-alive",
            "Keep-Alive": "timeout=600"
        }
    )

 


async def product_documentation_agent(latest_message: dict):
    """
    Processes user query and optional code context to send to DigitalOcean Product Documentation Agent.
    """
    config = {
        "api_base": "https://cluster-api.do-ai.run/v1",
        "agent_id": "eb07074f-f08c-11ef-bf8f-4e013e2ddde4",
        "agent_key": "p9NTzC59KD6c8e9Qjz8_2gDFrWJk0OGM",
        "agent_endpoint": "https://agent-bb7c8e8f107ffaca00e0-zo6gz.ondigitalocean.app/api/v1/"
    }

    pdocs_agent = AgentWrapper(config)

    # Extract user query
    user_query = latest_message.get("content", "").strip()

    # Extract code context (if available)
    code_contexts = []
    if latest_message.get("copilot_references"):
        for ref in latest_message["copilot_references"]:
            if ref.get("type") == "client.file" and "data" in ref and "content" in ref["data"]:  
                file_name = ref.get("id", "UNKNOWN FILE")
                code_content = ref["data"]["content"]
                code_contexts.append(f"\n\nFILENAME:\n{file_name}\n\nCODE CONTENT:\n{code_content}")

    # Concatenate all extracted code sections (if any)
    code_context = "\n\n---\n\n".join(code_contexts) if code_contexts else "NO CODE CONTEXT PROVIDED."

    # Use the imported prompt template
    agent_input = PROMPT_TEMPLATE.format(user_query=user_query, code_context=code_context)

    # Make the actual call async
    doc_response = await pdocs_agent.get_response(agent_input)

    print(doc_response)

    logging.info(doc_response)
    return doc_response
