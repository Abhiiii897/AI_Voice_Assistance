from sentiment_analysis import SentimentAnalyzer
import os
from dotenv import load_dotenv

load_dotenv()

analyzer = SentimentAnalyzer()

test_cases = [
    "hi",
    "thank you very much for your help",
    "this machine is broken and useless",
    "how do I calibrate the X axis?",
    "I've been waiting for hours and nobody is helping me!",
    "just checking properly",
    "I don't understand what you mean",
    "Why is the light blinking red?",
    "Hurry up, the machine is down!",
    "Can you explain how the sensor works?"
]

print("--- Starting Sentiment Analysis Test ---")

for text in test_cases:
    print(f"\nAnalyzing: '{text}'")
    result = analyzer.analyze(text)
    print(f"Result: {result}")

print("\n--- Test Complete ---")
