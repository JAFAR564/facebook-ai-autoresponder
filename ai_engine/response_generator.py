import redis
from transformers import pipeline
from dotenv import load_dotenv
import os
from textblob import TextBlob

load_dotenv()

class AIResponseGenerator:
    def __init__(self, persona_profile):
        self.persona = persona_profile
        # Load GPT-J model
        self.generator = pipeline("text-generation", model="EleutherAI/gpt-j-6B")
        # Connect to Redis
        self.redis = redis.Redis.from_url(os.getenv("REDIS_URL"))

    def generate_response(self, prompt):
        # Check if response is cached
        cached_response = self.redis.get(f"response:{prompt}")
        if cached_response:
            return cached_response.decode("utf-8")

        # Add persona context to the prompt
        enriched_prompt = f"{self.persona}\nRespond to: {prompt}"
        
        # Generate response using GPT-J
        response = self.generator(enriched_prompt, max_length=100, do_sample=True, temperature=0.7)
        generated_response = response[0]['generated_text']

        # Cache the response
        self.redis.set(f"response:{prompt}", generated_response)

        # Adjust response based on sentiment
        sentiment = self.analyze_sentiment(prompt)
        if sentiment == "negative":
            return "I'm sorry to hear that. How can I help?"
        else:
            return generated_response

    def analyze_sentiment(self, text):
        analysis = TextBlob(text)
        if analysis.sentiment.polarity > 0:
            return "positive"
        elif analysis.sentiment.polarity < 0:
            return "negative"
        else:
            return "neutral"