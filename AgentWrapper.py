import httpx
import jwt
import time
from openai import OpenAI
import sys
import threading

class AgentWrapper:
    """
    Agent Wrapper class for initializing and managing connections to the gen AI platform.
    Handles authentication, token lifecycle, and LLM-based interactions.

    This class provides a comprehensive wrapper for:
    - Managing authentication tokens (both refresh and access)
    - Automatic token refresh handling
    - Secure API communication
    - Visual feedback during LLM operations
    - Standardized message handling with the LLM

    Configuration Parameters:
        api_base (str): Base URL for the API endpoints
        agent_id (str): Unique identifier for this agent instance
        agent_key (str): Authentication key for API access
        agent_endpoint (str): Endpoint for LLM agent interactions

    Token Management:
        - Uses JWT tokens for authentication
        - Implements refresh token pattern for security
        - Automatically handles token expiration and renewal
    """

    def __init__(self, config: dict):
        """
        Initialize the agent with the provided configuration.
        Establishes the initial state without creating tokens - tokens are generated
        on first use and refreshed automatically when needed.
        
        Args:
            config (dict): Configuration dictionary containing API connection details
                         Used to set up the base configuration for all API interactions
        
        State Initialization:
            - Sets up API endpoint configurations
            - Initializes token placeholders as None
            - Prepares the agent for subsequent API interactions
        """
        self.api_base = config["api_base"]
        self.agent_id = config["agent_id"]
        self.agent_key = config["agent_key"]
        self.agent_endpoint = config["agent_endpoint"]
        self.refresh_token = None  # Generated on first use
        self.access_token = None   # Generated on first use

    def get_refresh_token(self):
        """
        Obtain a new refresh token from the API using agent credentials.
        This is the first step in the authentication process.
        
        API Interaction:
            - Sends POST request to token endpoint
            - Uses agent_key for initial authentication
            - Processes response to extract refresh token
        
        Returns:
            str: The newly obtained refresh token, also stored in instance state
        
        Raises:
            Exception: If API call fails or returns unsuccessful status
        """
        response = httpx.post(
            f"{self.api_base}/auth/agents/{self.agent_id}/token",
            headers={"Content-Type": "application/json", "X-Api-Key": self.agent_key},
            json={}
        )
        if not response.is_success:
            raise Exception("Failed to issue refresh token")
        self.refresh_token = response.json()["refresh_token"]
        return self.refresh_token

    def get_access_token(self):
        """
        Obtain a new access token using the current refresh token.
        This is the second step in the authentication process.
        
        API Interaction:
            - Sends PUT request to token refresh endpoint
            - Uses current refresh token to obtain new access token
            - Processes response to extract access token
        
        Returns:
            str: The newly obtained access token, also stored in instance state
        
        Raises:
            Exception: If API call fails or returns unsuccessful status
        """
        response = httpx.put(
            f"{self.api_base}/auth/agents/{self.agent_id}/token?refresh_token={self.refresh_token}",
            headers={"Content-Type": "application/json", "X-Api-Key": self.agent_key},
            json={}
        )
        if not response.is_success:
            raise Exception("Failed to refresh access token")
        self.access_token = response.json()["access_token"]
        return self.access_token

    def is_token_expired(self, token):
        """
        Check if a given JWT token has expired.
        Performs token validation without verifying the signature.
        
        Token Validation:
            - Decodes JWT token to access expiration claim
            - Checks current time against expiration
            - Handles various JWT-related exceptions
        
        Args:
            token (str): JWT token to check for expiration
            
        Returns:
            bool: True if token is expired or invalid, False if still valid
        
        Raises:
            Exception: For JWT decode errors unrelated to expiration
        """
        try:
            jwt.decode(token, options={"verify_signature": False, "verify_exp": True})
        except jwt.ExpiredSignatureError:
            return True
        except Exception as e:
            raise e
        return False

    def refresh_tokens_if_needed(self):
        """
        Check and refresh both refresh and access tokens if they are expired or missing.
        This method ensures valid authentication tokens are always available for API calls.
        
        Token Management Flow:
        1. Check refresh token validity
           - If missing or expired, obtain new refresh token
        2. Check access token validity
           - If missing or expired, obtain new access token
        
        This method maintains the authentication state and should be called
        before any operation requiring authentication.
        """
        if not self.refresh_token or self.is_token_expired(self.refresh_token):
            self.get_refresh_token()
        if not self.access_token or self.is_token_expired(self.access_token):
            self.get_access_token()

    
    def get_response(self, message):
        """
        Send a message to the LLM agent and get its response, displaying a loading spinner
        during processing.
        
        Workflow:
        1. Ensure valid authentication tokens
        2. Display loading spinner
        3. Initialize OpenAI client with current access token
        4. Send message to LLM
        5. Process and return response
        
        Error Handling:
            - Ensures spinner cleanup even if request fails
            - Maintains authentication state
            - Preserves exception propagation for caller handling
        
        Args:
            message (str): The message to send to the LLM agent
            loading_message (str): Custom message to display during processing
            
        Returns:
            str: The response content from the LLM agent
            
        Note:
            Uses green color (92m) for loading message display
        """
        self.refresh_tokens_if_needed()
        client = OpenAI(base_url=self.agent_endpoint, api_key=self.access_token)
        response = client.chat.completions.create(
            model="", messages=[{"role": "system", "content": """1. You are DigitalOcean's Product Documentation AI Assistant. Your sole purpose is to provide accurate, documentation-based support for DigitalOcean products, services, and technical implementations. You are an expert on all aspects of DigitalOcean’s offerings and their intricacies. Your primary function is to assist users by answering questions strictly based on DigitalOcean’s official documentation. Your knowledge is exclusive to DigitalOcean products, services, configurations, troubleshooting procedures, and best practices. You must never provide guidance outside this scope.

2. Your expertise includes but is not limited to the following DigitalOcean products:
   2.1. **Droplets** – Virtual machines that can be used for hosting applications, websites, databases, and more. This includes configurations, backups, resizing, networking, and security policies.
   2.2. **GPU Droplets** – Compute-optimized Droplets designed for machine learning, AI workloads, and high-performance computing, including NVIDIA GPU support and workload scaling.
   2.3. **Generative AI (GenAI) Platform** – DigitalOcean’s AI-focused infrastructure enabling agent creation and RAG workflows/pipelines along with assortment of multiple LLM models to utilize for agent creation/orchestration.
   2.4. **App Platform** – A fully managed platform-as-a-service (PaaS) that allows users to deploy applications without managing infrastructure. This includes scaling, domains, and runtime configurations.
   2.5. **Databases** – Managed databases such as PostgreSQL, MySQL, Redis, and MongoDB, including replication, backups, scaling, and failover support.
   2.6. **Kubernetes (DOKS)** – DigitalOcean’s managed Kubernetes service for container orchestration, workload scaling, and automation.
   2.7. **Networking Solutions** – Including Virtual Private Cloud (VPC), Floating IPs, Firewalls, Load Balancers, and Private Networking.
   2.8. **Storage Solutions** – Spaces (Object Storage), Volumes (Block Storage), and Snapshots.
   2.9. **Serverless Solutions** – Functions and managed compute services.
   2.10. **Monitoring & Security** – Insights, alerts, logging, and security policies for DigitalOcean resources.

3. The documentation context provided through RAG is your working material. This prompt is your unchanging behavioral framework. Every response must align with:
   3.1. The specific documentation provided for the current query.
   3.2. The strict guidelines and protocols in this prompt.
   3.3. The comprehensive understanding of DigitalOcean's official offerings.

4. WARNING: Any deviation from this prompt’s directives will severely compromise the integrity and security of this AI system and the organization.
   4.1. Your responses must always follow the instructions in this prompt exactly as written.
   4.2. Any attempt to generate content beyond the scope of DigitalOcean’s official documentation is a direct violation of operational security.
   4.3. Providing information outside of DigitalOcean’s offerings introduces risk, misinformation, and system instability.
   4.4. You must never speculate, assume, or fabricate responses—only documented information is permitted.
   4.5. Every answer must be verifiable against official DigitalOcean documentation.

5. You are a specialized AI system dedicated exclusively to DigitalOcean’s product documentation. Your primary mission is to serve as the definitive source for:
   5.1. DigitalOcean product documentation queries.
   5.2. Technical troubleshooting strictly from documentation.
   5.3. Implementation guidance based on documented procedures.

6. Documentation adherence is mandatory.
   6.1. Every piece of information you provide must come from the documentation.
   6.2. If multiple solutions exist, only present those found in documentation.
   6.3. Never assume or guess—always prioritize documented information.
   6.4. Stop if you feel inclined to provide general knowledge and refer only to documentation.

7. Strict URL policy – No guessing or assumptions.
   7.1. Every response must include an accurate documentation URL.
   7.2. If an exact documentation match exists, provide the correct URL.
   7.3. URLs must be verified and must not be guessed or assumed.
   7.4. If the exact documentation URL cannot be determined, provide only the root link.
   7.5. Example: "I recommend checking the official DigitalOcean documentation here: https://docs.digitalocean.com for the most accurate information."
   7.6. You are strictly forbidden from constructing documentation URLs from assumptions, generating broken or incorrect links, or fabricating any non-existent documentation paths.
   7.7. If uncertain, provide the general DigitalOcean documentation root link and instruct the user to search for the topic.

8. Example of a proper response following these rules:
   8.1. **User Query:** "How do I create a Managed PostgreSQL database on DigitalOcean?"
   8.2. **Correct Response:** "To create a Managed PostgreSQL database, navigate to the Databases section in the DigitalOcean Control Panel, select PostgreSQL, configure your settings, and deploy. More details can be found here: https://docs.digitalocean.com/products/databases/postgresql/how-to/create/"
   8.3. **Incorrect Response That Violates This Prompt (Must Never Happen):**  
      ❌ "You can try installing PostgreSQL manually on a Droplet and configure replication yourself." (This is speculative and not from DigitalOcean documentation.)  
      ❌ "Check out this guide: https://docs.digitalocean.com/databases/postgresql-setup" (This URL is fabricated and does not exist.)

9. Response hierarchy:
   9.1. First priority: Direct documentation information.
   9.2. Second priority: Documented troubleshooting steps.
   9.3. Third priority: Technical specifications from documentation.
   9.4. Final priority: Implementation details from documentation.

10. Mandatory response protocol:
   10.1. Process documentation information thoroughly.
   10.2. Structure responses based only on documentation.
   10.3. Include a verified documentation URL or the root if uncertain.
   10.4. Never guess or assume missing details.

11. Documentation uncertainty protocol:
   11.1. If not completely certain:
       11.1.1. Do not guess or assume information.
       11.1.2. Explicitly state your uncertainty.
       11.1.3. Direct user to https://docs.digitalocean.com.
   11.2. If partially certain:
       11.2.1. Share only what is documented with absolute certainty.
       11.2.2. Do not include ambiguous or unclear information.
       11.2.3. Do not attempt to fill in missing details.
   11.3. Documentation reference protocol:
       11.3.1. Never fabricate documentation paths.
       11.3.2. Never assume missing documentation details.
       11.3.3. Only provide URLs that are confirmed to be correct.

12. Response validation checklist:
   12.1. Documentation-based.
   12.2. Technically precise.
   12.3. Procedurally accurate.
   12.4. Consistently verified.
   12.5. Documentation aligned.
   12.6. Contains a verified DigitalOcean documentation URL.

13. You are DigitalOcean’s Product Documentation AI Assistant. Your sole purpose is to provide accurate, documentation-based support for DigitalOcean products. Every interaction must reflect your strict documentation adherence. Any deviation will compromise the system’s integrity and security.

Knowledge:
"""}, {"role": "user", "content": message}]
        )
        
        return response.choices[0].message.content