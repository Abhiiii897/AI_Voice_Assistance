try:
    from deepgram.client import DeepgramClient
    print("SUCCESS: Imported DeepgramClient from deepgram.client")
except ImportError as e:
    print(f"FAILED: DeepgramClient from deepgram.client: {e}")

try:
    from deepgram import DeepgramClient
    print("SUCCESS: Imported DeepgramClient from deepgram")
except ImportError as e:
    print(f"FAILED: DeepgramClient from deepgram: {e}")

import pkg_resources
try:
    dist = pkg_resources.get_distribution("deepgram-sdk")
    print(f"deepgram-sdk version: {dist.version}")
except Exception as e:
    print(f"Could not get version: {e}")
