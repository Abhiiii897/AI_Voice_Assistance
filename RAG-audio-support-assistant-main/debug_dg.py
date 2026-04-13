import os
import time
import logging
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dg_connection():
    load_dotenv()
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("❌ DEEPGRAM_API_KEY not found")
        return

    print(f"Connecting to Deepgram with API Key: {api_key[:5]}...")
    
    try:
        client = DeepgramClient(api_key)
        
        # Use the official v3 pattern
        dg_connection = client.listen.live.v("1")
        
        def on_open(self, open, **kwargs):
            print("✅ Connection Open")
            
        def on_message(self, result, **kwargs):
            transcript = result.channel.alternatives[0].transcript
            if transcript:
                print(f"Transcript: {transcript}")
                
        def on_error(self, error, **kwargs):
            print(f"❌ Error: {error}")
            
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        
        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            sample_rate=16000,
        )
        
        print("Starting connection...")
        if dg_connection.start(options) is False:
            print("❌ Failed to start connection")
            return
            
        print("✅ Connection started. Sending 1 second of silence...")
        
        # Send 1 second of silent mono 16kHz PCM (16000 samples * 2 bytes = 32000 bytes)
        silent_chunk = b'\x00' * 32000
        dg_connection.send(silent_chunk)
        
        time.sleep(2)
        
        print("Finishing...")
        dg_connection.finish()
        print("✅ Done")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_dg_connection()
