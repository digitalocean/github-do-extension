# **DigitalOcean GitHub Copilot Extension** 

## Running the Application

To start the application, follow these steps:

1. **Ensure you have Python 3.10+ installed.**  
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Run the FastAPI application using Uvicorn:**
   ```sh
   uvicorn server:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 600 --log-level info
   ```

---

## Setting Up the Forwarding URL

To integrate this extension with **GitHub Copilot**, follow these steps:

1. **Go to Developer Settings** in your GitHub App.  
2. **Paste the forwarding URL** into the **Agent URL** under Copilot settings.  
3. **Obtain the URL** from one of the following sources:

   - **Ngrok**: If using Ngrok, run:
     ```sh
     ngrok http 8000
     ```
     Copy the **generated HTTPS forwarding URL** and paste it into the **Agent URL** field.

   - **App Platform**: If deploying on **DigitalOcean App Platform**, use the assigned **public URL**.

Once configured, GitHub Copilot will send requests to your extension, enabling **real-time responses** within the Copilot chat UI.


## **Overview**  
We are developing a **DigitalOcean Extension for GitHub Copilot**, enabling users to interact directly with a **DigitalOcean agent** that specializes in:  
- **DigitalOcean documentation**  
- **Product insights**  
- **DO-specific recommendations**  

This extension is designed for users leveraging **DigitalOcean resources** and aims to provide **relevant, DO-oriented guidance** seamlessly within Copilot Chat.  

## **Development Background**  
This extension is built upon concepts outlined in **[this tutorial](https://neon.tech/blog/how-to-build-github-copilot-extensions)**, expanding it into a **FastAPI-based application** that integrates with DigitalOcean's agent system.  

## **Initial Implementation**  
The original idea was to:  
1. **Connect with the DigitalOcean extension** within GitHub Copilot Chat.  
2. **Forward queries (including attached code) to the DigitalOcean agent** for processing.  
3. **Send the agent's response to GitHub’s API** to **regurgitate** the exact DigitalOcean agent response.  

## **Problem with GitHub Copilot's API**  
### **Copilot Contradicting External Agent Knowledge**  
- Initially, responses from the DigitalOcean agent were sent to GitHub Copilot's API.  
- However, Copilot **often contradicted** the agent's responses, **favoring its own training data** over external sources.  
- This **defeated the purpose** of integrating DigitalOcean’s expertise into Copilot Chat.  

## **Alternative Approach**  
### **Replicating GitHub Copilot’s Streaming Response Format**  
- Instead of invoking GitHub's API, we **emulated the response structure** Copilot expects.  
- By **replicating Copilot’s streaming format**, we successfully **rendered responses** in the Copilot Chat UI **without** relying on GitHub’s API.  

## **Current Challenges**  
While short responses work for now, **longer or complex queries (including attached full code) trigger errors**, such as:  
- **“Internal agent error”**  
- **“GitHub was unable to connect to ‘doextension’”**  

These indicate **possible issues with**:  
1. **Timeouts** – GitHub Copilot may **drop connections if responses take too long**.  
2. **Rate Limits** – Requests to the DigitalOcean agent **might be exceeding thresholds**.  
3. **Streaming Issues** – The response stream **might not be keeping Copilot’s connection alive properly**.  

## **Next Steps**  
- **Understand what was triggering those error messages** as we need to accommodate longer more complex queries for this extension to work with zero exceptions.
- **Ensure immediate response streaming** to **keep the connection open** while waiting for the DigitalOcean agent.  
- **Investigate timeouts** and **adjust FastAPI/Uvicorn settings** to prevent premature disconnections.  
- **Optimize response chunking** to handle **longer** DigitalOcean agent outputs **without truncation**.  

Our goal is to **seamlessly integrate** the DigitalOcean agent into GitHub Copilot **without API contradictions**, ensuring **fully rendered responses** for complex queries.  

