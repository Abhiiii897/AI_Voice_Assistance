"""
Deepgram Speech-to-Text Integration

Uses Deepgram Nova-2 model for real-time transcription via WebSocket.
Fully asynchronous with proper error handling and connection management.

Configuration:
- API Key: Set DEEPGRAM_API_KEY in .env
- Model: nova-2 (production-grade, low latency)
- Encoding: linear16 (PCM audio)
- Sample Rate: 16000 Hz (16 kHz)
- Channels: 1 (mono)
"""
import threading
import logging
import time
from typing import Optional, Callable
from enum import Enum

import os
from dotenv import load_dotenv

# Import Deepgram SDK components
try:
    from deepgram.client import DeepgramClient
    from deepgram.listen.v1.client import V1Client
    from deepgram.core.events import EventType
    DEEPGRAM_AVAILABLE = True
except ImportError as e:
    DEEPGRAM_AVAILABLE = False
    print(f"[Transcriber Error] Deepgram SDK symbols missing: {e}")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptionModel(Enum):
    """Available Deepgram models"""
    NOVA_2 = "nova-2"  # Latest, fastest, most accurate
    NOVA = "nova"      # Previous generation
    ENHANCED = "enhanced"  # Enhanced tier
    BASE = "base"      # Base tier


class Transcriber:
    """
    Deepgram real-time transcription client.
    
    Handles WebSocket connection, audio streaming, and transcript callbacks.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: TranscriptionModel = TranscriptionModel.NOVA_2,
        on_processing_callback: Optional[Callable] = None,
        on_partial_transcript_callback: Optional[Callable] = None,
        on_error_callback: Optional[Callable] = None,
        language: str = "en",
        punctuate: bool = True,
        smart_format: bool = True,
        diarize: bool = False,
        utterance_end_ms: int = 1000
    ):
        """
        Initialize Deepgram transcriber.
        
        Args:
            api_key: Deepgram API key (defaults to DEEPGRAM_API_KEY env var)
            model: Transcription model to use (default: nova-2)
            on_processing_callback: Callback for final transcripts
            on_partial_transcript_callback: Callback for interim results
            on_error_callback: Callback for errors
            language: Language code (e.g., 'en', 'es', 'fr')
            punctuate: Add punctuation to transcripts
            smart_format: Format numbers, dates, currency
            diarize: Identify speakers (experimental)
            utterance_end_ms: Silence duration to consider phrase end (ms)
        """
        # Load env if api_key not provided
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("DEEPGRAM_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Deepgram API key not found. "
                "Set DEEPGRAM_API_KEY in .env or pass api_key parameter"
            )
        
        self.api_key = api_key
        self.model = model.value if isinstance(model, TranscriptionModel) else model
        self.on_processing_callback = on_processing_callback
        self.on_partial_callback = on_partial_transcript_callback
        self.on_error_callback = on_error_callback
        
        # Configuration
        self.language = language
        self.punctuate = punctuate
        self.smart_format = smart_format
        self.diarize = diarize
        self.utterance_end_ms = utterance_end_ms
        
        # State
        self.running = False
        self.listen_thread = None
        self.socket = None
        self.dg_client = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self._last_processed_text = ""
        self._last_processed_at = 0.0
        
        logger.info(f"Transcriber initialized (model: {self.model})")

    def start(self):
        """Start the transcriber."""
        if not DEEPGRAM_AVAILABLE:
            error_msg = "Deepgram SDK not available"
            logger.error(f"[Transcriber Error] {error_msg}")
            if self.on_error_callback:
                self.on_error_callback(error_msg)
            return False
        
        self.running = True
        logger.info("[Transcriber] Started")
        return True

    def stop(self):
        """Stop the transcriber and close connection."""
        self.running = False
        logger.info("[Transcriber] Stopped")

    def stream_audio(self, audio_generator):
        """
        Stream audio to Deepgram for transcription.
        
        Args:
            audio_generator: Generator yielding audio chunks (bytes)
        """
        if not DEEPGRAM_AVAILABLE:
            logger.error("Deepgram SDK not available")
            return

        try:
            self._stream_with_retry(audio_generator)
        except Exception as e:
            error_msg = f"Deepgram streaming failed: {e}"
            logger.error(f"[Transcriber Error] {error_msg}")
            if self.on_error_callback:
                self.on_error_callback(error_msg)

    def _stream_with_retry(self, audio_generator):
        """Stream with automatic reconnection logic."""
        self.reconnect_attempts = 0
        
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self._stream_internal(audio_generator)
                break  # Successful completion
            except Exception as e:
                self.reconnect_attempts += 1
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    wait_time = 2 ** self.reconnect_attempts  # Exponential backoff
                    logger.warning(
                        f"Stream error (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max reconnection attempts reached. Giving up.")
                    if self.on_error_callback:
                        self.on_error_callback(str(e))
                    raise

    def _stream_internal(self, audio_generator):
        """Internal streaming implementation using Deepgram SDK."""
        # Initialize Deepgram client
        self.dg_client = DeepgramClient(api_key=self.api_key)
        
        # Get V1 client for live transcription
        v1 = V1Client(client_wrapper=self.dg_client._client_wrapper)

        # Build connection options
        options = self._build_connection_options()
        
        logger.info("[Transcriber] Connecting to Deepgram...")
        
        # Connect using context manager
        with v1.connect(**options) as self.socket:
            
            # Setup event handlers
            self.socket.on(EventType.MESSAGE, self._on_message)
            self.socket.on(EventType.ERROR, self._on_error)
            self.socket.on(EventType.CLOSE, self._on_close)
            self.socket.on(EventType.OPEN, self._on_open)
            
            # Start listening in background thread
            self.listen_thread = threading.Thread(
                target=self.socket.start_listening,
                daemon=True,
                name="deepgram-listener"
            )
            self.listen_thread.start()
            
            logger.info("[Transcriber] Listening thread started")
            
            # Stream audio chunks
            bytes_sent = 0
            for chunk in audio_generator:
                if not self.running:
                    logger.info("[Transcriber] Stop signal received, closing stream")
                    break
                
                if chunk:
                    # Use send_media for older SDK pattern
                    self.socket.send_media(chunk)
                    bytes_sent += len(chunk)
            
            # Signal end of audio
            logger.info(f"[Transcriber] Sent {bytes_sent} bytes, closing connection")
            try:
                # Use finish() if available, otherwise manual CloseStream
                if hasattr(self.socket, 'finish'):
                    self.socket.finish()
                else:
                    self.socket._send({"type": "CloseStream"})
            except:
                pass

    def _build_connection_options(self) -> dict:
        """Build options dict for Deepgram connection."""
        options = {
            "model": self.model,
            "language": self.language,
            "encoding": "linear16",
            "sample_rate": 16000,
            "channels": 1,
            "smart_format": self.smart_format,
            "punctuate": self.punctuate,
            "interim_results": True,
            "utterance_end_ms": self.utterance_end_ms,
            "vad_events": True,
            "endpointing": 300,
        }
        
        if self.diarize:
            options["diarize"] = True
        
        return options

    def _on_open(self, *args, **kwargs):
        """Handle connection open event."""
        logger.info("[Deepgram] Connection OPEN")
        self.reconnect_attempts = 0  # Reset on successful connection

    def _on_message(self, result, **kwargs):
        """
        Handle transcript message from Deepgram.
        """
        # Log minimal info about result to verify reception
        logger.debug(f"[Deepgram] Received event: {getattr(result, 'type', type(result))}")
        
        try:
            # Handle transcript results
            if hasattr(result, 'channel'):
                channels = result.channel
                
                # Handle channel as list (Fern SDK pattern)
                channel = (
                    channels[0] 
                    if isinstance(channels, list) and channels 
                    else channels
                )
                
                # Skip if invalid
                if isinstance(channel, list):
                    logger.warning("[Deepgram] Received list of channels but empty or unexpected structure")
                    return
                
                # Extract transcript from alternatives
                if hasattr(channel, 'alternatives') and channel.alternatives:
                    alternatives = channel.alternatives
                    transcript = alternatives[0].transcript
                    
                    if transcript:
                        # Check if this is final result
                        is_final = getattr(result, 'is_final', False)
                        speech_final = getattr(result, 'speech_final', False)
                        
                        should_process = bool(speech_final or is_final)
                        if should_process:
                            now = time.time()
                            is_duplicate = (
                                transcript == self._last_processed_text
                                and (now - self._last_processed_at) < 1.2
                            )
                            if not is_duplicate:
                                logger.info(
                                    f"[Deepgram] FINAL (is_final={is_final}, speech_final={speech_final}): {transcript}"
                                )
                                self._last_processed_text = transcript
                                self._last_processed_at = now
                                if self.on_processing_callback:
                                    self.on_processing_callback(transcript)
                        else:
                            logger.info(f"[Deepgram] INTERIM (is_final={is_final}): {transcript}")
                            if self.on_partial_callback:
                                self.on_partial_callback(transcript)
            
            # Handle metadata or other events
            elif hasattr(result, 'type'):
                if result.type == "Metadata":
                    logger.info(f"[Deepgram] Metadata received: {getattr(result, 'request_id', 'no-id')}")
                elif result.type == "UtteranceEnd":
                    logger.debug("[Deepgram] Utterance end detected")

        except Exception as e:
            error_msg = f"Error processing message: {e}"
            logger.error(f"[Deepgram Error] {error_msg}")
            # Don't fail silently
            
    def _on_error(self, error, **kwargs):
        """Handle error event."""
        error_msg = str(error)
        logger.error(f"[Deepgram Error] Connection error: {error_msg}")
        if self.on_error_callback:
            self.on_error_callback(error_msg)

    def _on_close(self, *args, **kwargs):
        """Handle connection closed event."""
        logger.warning("[Deepgram] Connection CLOSED")


# Example usage
if __name__ == "__main__":
    # Simple test
    def test_transcriber():
        def on_final(text):
            print(f"✓ Final: {text}")
        
        def on_partial(text):
            print(f"◌ Interim: {text}")
        
        def on_error(error):
            print(f"✗ Error: {error}")
        
        transcriber = Transcriber(
            on_processing_callback=on_final,
            on_partial_transcript_callback=on_partial,
            on_error_callback=on_error
        )
        
        transcriber.start()
        logger.info("Transcriber initialized and ready")
        
        # Audio input would come from frontend
        # transcriber.stream_audio(audio_generator)
        
        transcriber.stop()

    test_transcriber()

