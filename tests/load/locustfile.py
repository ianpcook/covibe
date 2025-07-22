"""Load testing configuration for the Agent Personality System API."""

import json
import random
from typing import Dict, Any

from locust import HttpUser, task, between


class PersonalityAPIUser(HttpUser):
    """Simulates a user interacting with the personality API."""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def on_start(self):
        """Initialize user session."""
        self.personality_ids = []
        self.test_personalities = [
            "Tony Stark - genius inventor",
            "Sherlock Holmes - brilliant detective", 
            "Yoda - wise Jedi master",
            "Einstein - theoretical physicist",
            "Gandalf - wise wizard",
            "Batman - dark knight detective",
            "Hermione Granger - brilliant witch",
            "Spock - logical Vulcan",
            "Iron Man - armored superhero",
            "Professor X - telepathic mutant leader"
        ]
    
    @task(3)
    def create_personality(self):
        """Create a new personality configuration."""
        personality_data = {
            "description": random.choice(self.test_personalities),
            "user_id": f"load_test_user_{random.randint(1, 1000)}",
            "source": "api"
        }
        
        with self.client.post(
            "/api/personality",
            json=personality_data,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                result = response.json()
                self.personality_ids.append(result.get("id"))
                response.success()
            else:
                response.failure(f"Failed to create personality: {response.status_code}")
    
    @task(2)
    def get_personality(self):
        """Retrieve an existing personality configuration."""
        if not self.personality_ids:
            return
            
        personality_id = random.choice(self.personality_ids)
        with self.client.get(
            f"/api/personality/{personality_id}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get personality: {response.status_code}")
    
    @task(1)
    def update_personality(self):
        """Update an existing personality configuration."""
        if not self.personality_ids:
            return
            
        personality_id = random.choice(self.personality_ids)
        update_data = {
            "description": f"{random.choice(self.test_personalities)} - updated",
            "active": random.choice([True, False])
        }
        
        with self.client.put(
            f"/api/personality/{personality_id}",
            json=update_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to update personality: {response.status_code}")
    
    @task(2)
    def research_personality(self):
        """Test personality research endpoint."""
        research_data = {
            "query": random.choice(self.test_personalities),
            "include_sources": True
        }
        
        with self.client.post(
            "/api/personality/research",
            json=research_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "profiles" in result:
                    response.success()
                else:
                    response.failure("Research response missing profiles")
            else:
                response.failure(f"Research failed: {response.status_code}")
    
    @task(1)
    def detect_ide(self):
        """Test IDE detection endpoint."""
        with self.client.get(
            "/api/ide/detect",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"IDE detection failed: {response.status_code}")
    
    @task(1)
    def delete_personality(self):
        """Delete a personality configuration."""
        if not self.personality_ids:
            return
            
        personality_id = self.personality_ids.pop()
        with self.client.delete(
            f"/api/personality/{personality_id}",
            catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to delete personality: {response.status_code}")


class ChatUser(HttpUser):
    """Simulates a user interacting with the chat interface."""
    
    wait_time = between(2, 8)  # Longer wait times for chat interactions
    
    def on_start(self):
        """Initialize chat session."""
        self.session_id = f"chat_session_{random.randint(1, 10000)}"
        self.chat_messages = [
            "I want my agent to be like Tony Stark",
            "Make it more friendly and less sarcastic",
            "Can you make the agent sound like Yoda?",
            "I need a professional but approachable personality",
            "Make the agent sound like Sherlock Holmes",
            "Can you adjust the formality level?",
            "That looks good, please configure it",
            "Yes, that's perfect"
        ]
    
    @task
    def send_chat_message(self):
        """Send a chat message."""
        message_data = {
            "message": random.choice(self.chat_messages),
            "session_id": self.session_id
        }
        
        with self.client.post(
            "/api/chat/message",
            json=message_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "response" in result:
                    response.success()
                else:
                    response.failure("Chat response missing response field")
            else:
                response.failure(f"Chat message failed: {response.status_code}")


class WebSocketUser(HttpUser):
    """Simulates WebSocket connections for real-time features."""
    
    wait_time = between(3, 10)
    
    @task
    def websocket_connection_test(self):
        """Test WebSocket connection establishment."""
        # Note: This is a simplified test. Real WebSocket testing would require
        # additional libraries like websocket-client
        with self.client.get(
            "/api/ws/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"WebSocket health check failed: {response.status_code}")


# Load testing scenarios
class LightLoadUser(PersonalityAPIUser):
    """Light load scenario - normal usage patterns."""
    weight = 3
    wait_time = between(2, 8)


class HeavyLoadUser(PersonalityAPIUser):
    """Heavy load scenario - intensive usage."""
    weight = 1
    wait_time = between(0.5, 2)


class ChatOnlyUser(ChatUser):
    """Chat-focused user scenario."""
    weight = 2


class LLMLoadUser(HttpUser):
    """Simulates LLM-specific load testing scenarios."""
    
    wait_time = between(1, 3)  # Faster requests to test rate limiting
    
    def on_start(self):
        """Initialize LLM load testing session."""
        self.personality_descriptions = [
            "A brilliant but arrogant surgeon who becomes a mystical protector",
            "An innovative tech entrepreneur who revolutionized multiple industries", 
            "A wise mentor figure who guides heroes through difficult challenges",
            "A complex anti-hero with a troubled past but noble intentions",
            "An eccentric scientist who makes groundbreaking discoveries",
            "A charismatic leader who inspires others to achieve greatness",
            "A mysterious detective with extraordinary deductive abilities",
            "A compassionate healer who puts others' needs before their own",
            "A rebellious hacker who fights against corporate oppression",
            "A stoic warrior with an unbreakable code of honor"
        ]
        self.llm_providers = ["openai", "anthropic", "local"]
        self.request_count = 0
    
    @task(4)
    def llm_personality_research(self):
        """Test LLM-enhanced personality research with rate limiting."""
        self.request_count += 1
        
        research_data = {
            "description": random.choice(self.personality_descriptions),
            "use_cache": random.choice([True, False])
        }
        
        # Rotate through LLM providers to test switching
        provider = self.llm_providers[self.request_count % len(self.llm_providers)]
        
        with self.client.post(
            f"/api/personality/research?use_llm=true&llm_provider={provider}",
            json=research_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "profiles" in result:
                    # Check if LLM was actually used
                    if result.get("llm_used"):
                        response.success()
                    else:
                        # LLM fallback occurred - still success but note it
                        response.success()
                        print(f"LLM fallback occurred for provider {provider}")
                else:
                    response.failure("LLM research response missing profiles")
            elif response.status_code == 429:
                # Rate limiting - expected behavior
                response.success()
                print(f"Rate limited by {provider} provider")
            else:
                response.failure(f"LLM research failed: {response.status_code}")
    
    @task(3) 
    def llm_personality_creation(self):
        """Test LLM-enhanced personality creation."""
        personality_data = {
            "description": random.choice(self.personality_descriptions),
            "source": "load_test",
            "user_id": f"llm_load_user_{random.randint(1, 1000)}"
        }
        
        provider = random.choice(self.llm_providers)
        
        with self.client.post(
            f"/api/personality/?use_llm=true&llm_provider={provider}",
            json=personality_data,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                result = response.json()
                if result.get("profile"):
                    response.success()
                else:
                    response.failure("LLM personality creation missing profile")
            elif response.status_code == 429:
                # Rate limiting
                response.success()
                print(f"Rate limited during personality creation with {provider}")
            else:
                response.failure(f"LLM personality creation failed: {response.status_code}")
    
    @task(2)
    def llm_provider_status(self):
        """Check LLM provider status and health."""
        with self.client.get(
            "/api/personality/llm/status",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "providers" in result:
                    response.success()
                    
                    # Log provider availability for monitoring
                    providers = result["providers"]
                    for provider_name, provider_info in providers.items():
                        if not provider_info.get("available", True):
                            print(f"Provider {provider_name} unavailable")
                else:
                    response.failure("LLM status response missing providers")
            else:
                response.failure(f"LLM status check failed: {response.status_code}")
    
    @task(1)
    def concurrent_llm_requests(self):
        """Test concurrent LLM requests to trigger rate limiting."""
        import threading
        import time
        
        def make_request(request_id: int):
            """Make a single LLM request."""
            data = {
                "description": f"Concurrent test personality {request_id}",
                "use_cache": False  # Force LLM call
            }
            
            try:
                response = self.client.post(
                    "/api/personality/research?use_llm=true&llm_provider=openai",
                    json=data,
                    timeout=30
                )
                return response.status_code, request_id
            except Exception as e:
                return 500, request_id
        
        # Launch 5 concurrent requests
        threads = []
        results = []
        
        start_time = time.time()
        
        for i in range(5):
            thread = threading.Thread(target=lambda i=i: results.append(make_request(i)))
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join(timeout=45)  # 45 second timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Analyze results
        success_count = len([r for r in results if r and r[0] == 200])
        rate_limited_count = len([r for r in results if r and r[0] == 429])
        
        if success_count + rate_limited_count >= 3:  # At least 3 requests completed
            # Log concurrent request performance
            print(f"Concurrent LLM test: {success_count} success, {rate_limited_count} rate limited, {duration:.2f}s")
        else:
            print(f"Concurrent LLM test failed: only {success_count + rate_limited_count} requests completed")


class LLMStressUser(LLMLoadUser):
    """High-intensity LLM load testing."""
    weight = 1
    wait_time = between(0.1, 0.5)  # Very fast requests to stress test rate limiting


class LLMNormalUser(LLMLoadUser):
    """Normal LLM usage patterns."""
    weight = 3
    wait_time = between(2, 5)  # Normal usage timing


class MixedLLMUser(HttpUser):
    """Mixed usage - both LLM and traditional methods."""
    weight = 2
    wait_time = between(1, 4)
    
    def on_start(self):
        """Initialize mixed usage session."""
        self.test_descriptions = [
            "Sherlock Holmes",  # Well-known, should work with both methods
            "Mysterious innovative personality",  # Should work better with LLM
            "Yoda",  # Well-known
            "Complex multi-faceted character with contradictions"  # LLM preferred
        ]
    
    @task(2)
    def traditional_research(self):
        """Use traditional research method."""
        data = {
            "description": random.choice(self.test_descriptions),
            "use_cache": True
        }
        
        with self.client.post(
            "/api/personality/research?use_llm=false",
            json=data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("llm_used") is False:
                    response.success()
                else:
                    response.failure("Traditional research incorrectly used LLM")
            else:
                response.failure(f"Traditional research failed: {response.status_code}")
    
    @task(3)
    def llm_research(self):
        """Use LLM research method."""
        data = {
            "description": random.choice(self.test_descriptions),
            "use_cache": random.choice([True, False])
        }
        
        provider = random.choice(["openai", "anthropic"])
        
        with self.client.post(
            f"/api/personality/research?use_llm=true&llm_provider={provider}",
            json=data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()  # Rate limiting is expected
            else:
                response.failure(f"LLM research failed: {response.status_code}")