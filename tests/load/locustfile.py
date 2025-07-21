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