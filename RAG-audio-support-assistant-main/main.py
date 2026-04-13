from gevent import monkey
monkey.patch_all()

import json
import os
import time
import queue
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

from transcription import Transcriber
from rag_search import RAGSearcher
from sentiment_analysis import SentimentAnalyzer
from llm_suggestions import SuggestionGenerator

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'audio-rag-support-secret-key-2026'

# Enable CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Initialize SocketIO with gevent
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='gevent',
    ping_timeout=60,
    ping_interval=25,
    logger=False,
    engineio_logger=False
)

# Global state per session
sessions = {}

print("=" * 80)
print("🚀 Audio RAG Support Assistant - Complete Backend")
print("=" * 80)

# Initialize components (shared across sessions)
print("\n[INIT] Loading RAG system...")
try:
    rag = RAGSearcher()
    doc_count = rag.get_collection_stats().get('total_chunks', 0)
    print(f"[INIT] ✅ RAG system loaded! ({doc_count} document chunks)")
except Exception as e:
    print(f"[INIT] ⚠️ RAG system error: {e}")
    print("[INIT] ⚠️ Make sure you've run: python ingest_docs.py --input data/manuals/")
    rag = None

print("[INIT] Loading Gemini services...")
sentiment_analyzer = SentimentAnalyzer(api_key=os.getenv("GOOGLE_API_KEY"))
suggestion_gen = SuggestionGenerator(api_key=os.getenv("GOOGLE_API_KEY"))
print("[INIT] ✅ Gemini services ready!")

class SessionData:
    """Manages data for a single user session"""
    def __init__(self, session_id):
        self.session_id = session_id
        self.transcripts = []
        self.audio_queue = queue.Queue()
        self.suggestion_queue = queue.Queue() # New queue for AI processing
        self.transcriber = None
        self.is_recording = False
        self.ai_worker_active = False
        self.last_suggestion_key = None


def normalize_sentiment(value, text=None):
    """Map analyzer output to UI-supported sentiment labels."""
    v = (value or "Neutral").strip().lower()
    t = (text or "").strip().lower()

    positive_hits = sum(
        1 for k in ["thanks", "thank you", "great", "awesome", "perfect", "fixed", "resolved"]
        if k in t
    )
    agitated_hits = sum(
        1 for k in [
            "urgent", "asap", "immediately", "frustrat", "angry", "annoy", "worst",
            "still not", "again", "can't", "cannot", "not working", "stopped working"
        ]
        if k in t
    )
    negative_hits = sum(
        1 for k in [
            "error", "alarm", "fault", "failed", "fail", "problem", "issue", "broken",
            "stuck", "leak", "noise", "overheat", "overload"
        ]
        if k in t
    )

    if v in ("positive",):
        return "Positive"
    if v in ("negative",):
        return "Negative"
    if v in ("agitated", "frustrated", "urgent"):
        return "Agitated"
    if v in ("curious", "confused", "neutral"):
        if agitated_hits >= 1:
            return "Agitated"
        if negative_hits >= 2:
            return "Negative"
        if positive_hits >= 1:
            return "Positive"
        return "Neutral"

    if agitated_hits >= 1:
        return "Agitated"
    if negative_hits >= 2:
        return "Negative"
    if positive_hits >= 1:
        return "Positive"
    return "Neutral"


def normalize_category(value, text=None):
    """Map analyzer output to the 3-card UI taxonomy."""
    v = (value or "").strip().lower()
    t = (text or "").strip().lower()

    if t:
        if any(k in t for k in [
            "maintenance", "maintain", "service", "replace", "lubricat",
            "filter", "grease", "oil", "bearing", "spare", "parts"
        ]):
            return "Maintenance & Parts"
        if any(k in t for k in [
            "error", "alarm", "fault", "trip", "fail", "failed", "not working",
            "stuck", "overload", "axis", "servo", "drive", "spindle", "sensor",
            "pressure", "vacuum", "leak", "noise", "vibration"
        ]):
            return "Technical Troubleshooting"
        if any(k in t for k in [
            "how to", "how do i", "what is", "where is", "setup", "calibrate",
            "operation", "operate", "start", "mode", "program", "nc", "g-code"
        ]):
            return "Machine Operation"

    if v == "maintenance & parts":
        return "Maintenance & Parts"
    if v in ("technical troubleshooting", "software & controls"):
        return "Technical Troubleshooting"
    if v in ("calibration & setup", "general inquiry", "machine operation"):
        return "Machine Operation"
    return "Uncategorized"


def append_session_log(session_id, kind, payload):
    """Append JSONL log entries by session and channel type."""
    log_dir = os.path.join("logs", "sessions")
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, f"{session_id}_{kind}.jsonl")
    record = {"ts": time.time(), **payload}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def normalize_audio_chunk(data):
    """Normalize Socket.IO audio payloads into raw PCM bytes."""
    if isinstance(data, (bytes, bytearray, memoryview)):
        return bytes(data)

    if isinstance(data, list):
        try:
            return bytes(data)
        except Exception:
            return None

    if isinstance(data, dict):
        # Placeholder packets are transport metadata, not audio.
        if data.get('_placeholder') is True:
            return None

        # Defensive fallback for dict payloads with numeric keys.
        try:
            numeric_keys = sorted(
                (int(k) for k in data.keys() if str(k).isdigit()),
                key=int
            )
            if not numeric_keys:
                return None
            return bytes(
                data[str(k)] if str(k) in data else data[k]
                for k in numeric_keys
            )
        except Exception:
            return None

    return None

def get_session(session_id):
    """Get or create session data"""
    if session_id not in sessions:
        sessions[session_id] = SessionData(session_id)
    return sessions[session_id]

def suggestion_processor_worker(session_id):
    """
    Dedicated worker thread for RAG search and Gemini suggestions.
    Separates heavy LLM processing from the real-time audio stream.
    """
    session = get_session(session_id)
    session.ai_worker_active = True
    print(f"[AI-Worker {session_id[:8]}] Started")

    while session.is_recording or not session.suggestion_queue.empty():
        try:
            # Wait for a new transcript to process
            item = session.suggestion_queue.get(timeout=2)
            if item is None: break

            # Extract text and sentiment
            text = ""
            sentiment = None
            
            if isinstance(item, dict):
                text = item.get('text', '')
                sentiment = item.get('sentiment')
            else:
                text = str(item)

            pending_items = session.suggestion_queue.qsize()
            if pending_items > 0:
                # Skip stale items and process the newest context to reduce LLM burst traffic.
                print(
                    f"[AI-Worker {session_id[:8]}] Skipping stale suggestion item "
                    f"(pending={pending_items})"
                )
                session.suggestion_queue.task_done()
                continue

            print(f"[AI-Worker {session_id[:8]}] Processing suggestions for: {text[:50]}...")

            # Build recent context once for RAG + LLM
            full_context = " ".join(session.transcripts[-3:]).strip()
            if not full_context:
                full_context = text

            # 1. Search Knowledge Base
            results = []
            if rag:
                results = rag.search(full_context, top_k=3)
            else:
                print("[AI-Worker] ⚠️ RAG not loaded, using general knowledge only")

            if not results:
                print("[AI-Worker] ⚠️ No documents found, using general knowledge only")

            # 2. Get AI Insights (Summaries + Suggestions)
            context_docs = [r.text for r in results]
            
            # Keep track of source information for references with page/section
            source_map = {}
            for i, r in enumerate(results):
                # Extract page number (from chunk_index or metadata)
                page_num = r.metadata.get('page_number', r.chunk_index + 1)
                
                # Extract section name (from metadata or first line of text)
                section = r.metadata.get('section_name')
                if not section or section == "N/A":
                    # Try to extract from first line of chunk
                    first_line = r.text.split('\n')[0].strip()
                    if 0 < len(first_line) < 100:
                        section = first_line
                    else:
                        section = "Technical Details"
                
                source_map[i] = {
                    'name': os.path.basename(r.source) if r.source else "Manual",
                    'page': page_num,
                    'section': section,
                    'score': int(r.similarity_score * 100)
                }
            
            gemini_data = suggestion_gen.generate_suggestions(
                conversation_history=full_context,
                context_docs=context_docs,
                sentiment=sentiment
            )

            # 3. Emit Documentation Sources (Raw manual references)
            documentation = [{
                'title': os.path.basename(r.source),
                'relevance': int(r.similarity_score * 100)
            } for r in results]

            socketio.emit('knowledge_base', {
                'documentation': documentation,
                'sid': session_id[:8]
            }, room=session_id)

            # 4. Process References from Gemini (Convert indices to source names)
            doc_references = gemini_data.get("doc_references", [])
            formatted_references = []
            
            for ref in doc_references:
                source_idx = ref.get("source_index")
                match_score = ref.get("match_score", 0)
                
                if source_idx in source_map and match_score >= 40:
                    source_info = source_map[source_idx]
                    formatted_references.append({
                        "document": source_info['name'],
                        "page": source_info['page'],
                        "section": source_info['section'],
                        "match": match_score
                    })

            # If Gemini doesn't return references, fall back to top RAG results so UI source is still accurate.
            if not formatted_references and results:
                for i, _ in enumerate(results[:3]):
                    source_info = source_map.get(i)
                    if not source_info:
                        continue
                    formatted_references.append({
                        "document": source_info["name"],
                        "page": source_info["page"],
                        "section": source_info["section"],
                        "match": source_info["score"],
                    })

            # De-duplicate references while preserving best score ordering.
            deduped_refs = {}
            for ref in formatted_references:
                key = (ref.get("document"), ref.get("page"), ref.get("section"))
                prev = deduped_refs.get(key)
                if prev is None or ref.get("match", 0) > prev.get("match", 0):
                    deduped_refs[key] = ref
            formatted_references = sorted(
                deduped_refs.values(),
                key=lambda r: r.get("match", 0),
                reverse=True
            )
            
            # 5. Emit Combined AI Suggestions (with converted references)
            suggestions = gemini_data.get("suggestions", [])
            top_match = max([r.get("match", 0) for r in formatted_references], default=75)
            ui_category = normalize_category(
                sentiment.get('category') if isinstance(sentiment, dict) else "",
                text=full_context
            )

            normalized_suggestions = []
            for s in suggestions:
                item = dict(s) if isinstance(s, dict) else {"title": "Answer", "description": str(s)}
                item["title"] = item.get("title") or "Answer"
                item["category"] = normalize_category(
                    item.get("category", ui_category),
                    text=f"{item.get('description', '')} {full_context}"
                )
                rel = item.get("relevance", top_match)
                try:
                    rel_value = float(rel)
                    if rel_value <= 1:
                        rel_value = rel_value * 100
                except Exception:
                    rel_value = float(top_match)
                item["relevance"] = max(40.0, min(99.0, rel_value))
                if formatted_references:
                    top_ref = formatted_references[0]
                    item["source"] = {
                        "manual": top_ref.get("document", "Manual"),
                        "section": top_ref.get("section", "General"),
                        "page": top_ref.get("page", 1),
                    }
                normalized_suggestions.append(item)

            suggestions = normalized_suggestions
            suggestion_key = json.dumps(
                {
                    "suggestions": suggestions,
                    "references": formatted_references if formatted_references else []
                },
                sort_keys=True,
                ensure_ascii=False
            )

            if suggestion_key == session.last_suggestion_key:
                print(f"[AI-Worker {session_id[:8]}] Skipping duplicate suggestion payload")
                session.suggestion_queue.task_done()
                continue

            socketio.emit('ai_suggestions', {
                'suggestions': suggestions,
                'references': formatted_references if formatted_references else None,
                'sid': session_id[:8]
            }, room=session_id)
            session.last_suggestion_key = suggestion_key
            append_session_log(
                session_id,
                "suggestions",
                {
                    "suggestions": suggestions,
                    "references": formatted_references if formatted_references else []
                }
            )

            print(f"[AI-Worker {session_id[:8]}] ✅ Emitted {len(suggestions)} suggestions with {len(formatted_references)} references")
            session.suggestion_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"[AI-Worker {session_id[:8]}] ERROR: {e}")
            import traceback
            traceback.print_exc()

    session.ai_worker_active = False
    print(f"[AI-Worker {session_id[:8]}] Stopped")

def process_final_transcript(session_id, text):
    """Process final transcript: Emit immediately, then queue AI work"""
    session = get_session(session_id)
    session.transcripts.append(text)
    append_session_log(session_id, "transcript", {"text": text, "is_final": True})
    
    print(f"\n[Session {session_id[:8]}] FINAL: {text}")
    
    # 1. Send text to UI immediately
    socketio.emit('transcript', {
        'type': 'transcript',
        'text': text,
        'isFinal': True,
        'timestamp': int(time.time() * 1000),
    }, room=session_id)
    
    # 2. Analyze sentiment
    sentiment = {'sentiment': 'Neutral', 'category': 'Machine Operation'}
    try:
        raw_sentiment = sentiment_analyzer.analyze(text)
        sentiment = {
            'sentiment': normalize_sentiment(raw_sentiment.get('sentiment', 'Neutral'), text=text),
            'category': normalize_category(raw_sentiment.get('category', 'Machine Operation'), text=text)
        }
        socketio.emit('sentiment', {
            'sentiment': sentiment.get('sentiment', 'Neutral'),
            'category': sentiment.get('category', 'Machine Operation')
        }, room=session_id)
    except Exception as e:
        print(f"[ERROR] Sentiment failed: {e}")
    # 3. Queue RAG/LLM work for the Suggestion Worker (Seperate thread)
    session.suggestion_queue.put({'text': text, 'sentiment': sentiment})


def process_partial_transcript(session_id, text):
    """Process partial transcript"""
    # Don't print partials to terminal to avoid noise, just emit
    socketio.emit('transcript', {
        'type': 'transcript',
        'text': text,
        'isFinal': False,
        'timestamp': int(time.time() * 1000),
    }, room=session_id)

def audio_stream_worker(session_id):
    """Background worker to stream audio to Deepgram"""
    session = get_session(session_id)
    
    print(f"[Worker {session_id[:8]}] Starting audio stream worker...")
    
    # Create transcriber with callbacks
    def on_transcriber_error(error_text):
        print(f"[Worker {session_id[:8]}] Deepgram error: {error_text}")
        socketio.emit('transcription_error', {
            'type': 'transcription_error',
            'message': str(error_text)
        }, room=session_id)

    session.transcriber = Transcriber(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        on_processing_callback=lambda text: process_final_transcript(session_id, text),
        on_partial_transcript_callback=lambda text: process_partial_transcript(session_id, text),
        on_error_callback=on_transcriber_error,
        utterance_end_ms=1200  # Balanced pause threshold: responsive but still conversational
    )
    
    try:
        # Start Deepgram connection
        if not session.transcriber.start():
             print(f"[Worker {session_id[:8]}] ERROR: Failed to start transcriber (Check logs/env)")
             return
             
        print(f"[Worker {session_id[:8]}] ✅ Deepgram connected (waiting for audio...)")
        
        # Audio generator from queue
        def audio_generator():
            chunk_count = 0
            total_bytes = 0
            while session.is_recording:
                try:
                    # Get audio chunk from queue (with timeout)
                    chunk = session.audio_queue.get(timeout=1)
                    if chunk is None:
                        break
                    
                    chunk_count += 1
                    total_bytes += len(chunk)
                    
                    # Log every 50 chunks (approx 5-10 seconds)
                    if chunk_count % 50 == 0:
                        print(f"[Worker {session_id[:8]}] Streamed {chunk_count} chunks ({total_bytes/1024:.1f} KB) to Deepgram")
                        
                    yield chunk
                except queue.Empty:
                    continue
        
        # Stream audio to Deepgram
        session.transcriber.stream_audio(audio_generator())
        
    except Exception as e:
        print(f"[Worker {session_id[:8]}] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if session.transcriber:
            session.transcriber.stop()
        print(f"[Worker {session_id[:8]}] Audio stream worker stopped")

# HTTP Routes
@app.route('/')
def index():
    return {
        'service': 'Audio RAG Support Assistant',
        'status': 'running',
        'version': '1.0.0',
        'components': {
            'transcription': 'Deepgram Nova-2',
            'rag': f'{rag.get_collection_stats().get("total_chunks", 0)} chunks' if rag else 'Not loaded',
            'llm': 'Gemini 2.0 Flash'
        }
    }, 200

@app.route('/health')
def health():
    return {
        'status': 'ok',
        'services': {
            'rag': rag is not None,
            'rag_chunks': rag.get_collection_stats().get('total_chunks', 0) if rag else 0,
            'sentiment': True,
            'suggestions': True,
            'websocket': True,
            'deepgram': os.getenv("DEEPGRAM_API_KEY") is not None,
            'gemini': os.getenv("GOOGLE_API_KEY") is not None
        }
    }, 200

@app.route('/api/audio', methods=['POST'])
def receive_audio():
    """Receive audio chunks from frontend"""
    session_id = request.headers.get('X-Session-ID', 'default')
    session = get_session(session_id)
    
    if session.is_recording:
        audio_chunk = request.get_data()
        session.audio_queue.put(audio_chunk)
        return {'status': 'received', 'bytes': len(audio_chunk)}, 200
    else:
        return {'status': 'not_recording'}, 400


@app.route('/api/logs/<session_id>/<kind>', methods=['GET'])
def get_session_logs(session_id, kind):
    """Retrieve session logs by kind: transcript|suggestions|notes."""
    if kind not in {"transcript", "suggestions", "notes"}:
        return {"error": "Invalid log kind"}, 400

    path = os.path.join("logs", "sessions", f"{session_id}_{kind}.jsonl")
    if not os.path.exists(path):
        return {"session_id": session_id, "kind": kind, "entries": []}, 200

    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                continue

    return {"session_id": session_id, "kind": kind, "entries": entries}, 200

# WebSocket Events
@socketio.on('connect')
def handle_connect(auth=None):
    session_id = request.sid
    print(f"\n[WebSocket] [OK] Client connected: {session_id[:8]}...")
    
    # Ensure session data exists
    get_session(session_id)
    
    # Join room for this session
    from flask_socketio import join_room
    join_room(session_id)
    
    emit('connected', {
        'type': 'connected',
        'message': 'Connected to Audio RAG Support Backend',
        'session_id': session_id,
        'rag_available': rag is not None,
        'rag_chunks': rag.get_collection_stats().get('total_chunks', 0) if rag else 0
    })

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    print(f"\n[WebSocket] ❌ Client disconnected: {session_id[:8]}...")
    
    # Stop recording if active
    if session_id in sessions:
        session = sessions[session_id]
        session.is_recording = False
        session.audio_queue.put(None) # Break the audio generator loop
        
        if session.transcriber:
            try:
                session.transcriber.stop()
            except Exception as e:
                print(f"Error stopping transcriber: {e}")
        
        # Clean up session
        del sessions[session_id]

@socketio.on('start_recording')
def handle_start_recording():
    session_id = request.sid
    session = get_session(session_id)

    if session.is_recording:
        emit('recording_started', {
            'type': 'recording_started',
            'status': 'already_recording',
            'message': 'Recording is already active'
        })
        return
    
    print(f"\n[Recording] Starting for session {session_id[:8]}...")
    
    # Reset session data
    session.transcripts = []
    session.is_recording = True
    session.last_suggestion_key = None
    
    # 1. Start audio streaming worker (Deepgram)
    import gevent
    gevent.spawn(audio_stream_worker, session_id)

    # 2. Start AI suggestion worker (RAG + Gemini)
    gevent.spawn(suggestion_processor_worker, session_id)
    
    emit('recording_started', {
        'type': 'recording_started',
        'status': 'success',
        'message': 'Recording started - speak now!'
    })

@socketio.on('stop_recording')
def handle_stop_recording():
    session_id = request.sid
    session = get_session(session_id)

    if not session.is_recording:
        emit('recording_stopped', {
            'type': 'recording_stopped',
            'status': 'already_stopped',
            'transcript_count': len(session.transcripts)
        })
        return
    
    print(f"\n[Recording] Stopping for session {session_id[:8]}...")
    
    session.is_recording = False
    session.audio_queue.put(None)  # Signal to stop
    
    emit('recording_stopped', {
        'type': 'recording_stopped',
        'status': 'success',
        'transcript_count': len(session.transcripts)
    })

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    """Handle audio chunk from frontend via WebSocket"""
    session_id = request.sid
    session = get_session(session_id)
    
    normalized = normalize_audio_chunk(data)

    # Log every chunk with type and size (briefly)
    if not hasattr(session, '_total_bytes'): session._total_bytes = 0
    if not hasattr(session, '_chunk_count'): session._chunk_count = 0
    if not hasattr(session, '_dropped_chunks'): session._dropped_chunks = 0
    
    session._chunk_count += 1
    if normalized:
        session._total_bytes += len(normalized)
    else:
        session._dropped_chunks += 1
    
    # Log heartbeats frequently to confirm low latency
    if session._chunk_count % 20 == 0:
        datatype = type(data).__name__
        print(
            f"[Audio {session_id[:8]}] chunks={session._chunk_count} "
            f"bytes={session._total_bytes} dropped={session._dropped_chunks} type={datatype}"
        )
    
    if session.is_recording and normalized:
        session.audio_queue.put(normalized)


@socketio.on('note_added')
def handle_note_added(data):
    """Persist note events for the current session."""
    session_id = request.sid
    note_text = ""
    if isinstance(data, dict):
        note_text = str(data.get("text", "")).strip()
    elif isinstance(data, str):
        note_text = data.strip()
    if not note_text:
        return
    append_session_log(
        session_id,
        "notes",
        {
            "id": data.get("id") if isinstance(data, dict) else None,
            "text": note_text,
            "timestamp": data.get("timestamp") if isinstance(data, dict) else time.time()
        }
    )

@socketio.on('test_rag')
def handle_test_rag(data):
    """Test RAG search with a query"""
    query = data.get('query', 'machine troubleshooting')
    
    print(f"\n[Test RAG] Query: {query}")
    
    if rag:
        results = rag.search(query, top_k=3)
        
        emit('rag_test_result', {
            'query': query,
            'found': len(results),
            'results': [
                {
                    'source': r.source,
                    'preview': r.text[:200],
                    'similarity': r.similarity_score
                }
                for r in results
            ]
        })
    else:
        emit('rag_test_result', {
            'query': query,
            'found': 0,
            'error': 'RAG not loaded'
        })

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🎯 Server Configuration")
    print("=" * 80)
    print("\n📡 Endpoints:")
    print("  • HTTP Server: http://localhost:5001")
    print("  • WebSocket: ws://localhost:5001/socket.io/")
    print("  • Health Check: http://localhost:5001/health")
    print("\n🤖 AI Services:")
    print(f"  • Deepgram: {'✅ Configured' if os.getenv('DEEPGRAM_API_KEY') else '❌ Missing'}")
    print(f"  • Gemini: {'✅ Configured' if os.getenv('GOOGLE_API_KEY') else '❌ Missing'}")
    print(f"  • RAG: {'✅ Ready' if rag else '❌ Not loaded'}")
    if rag:
        print(f"  • Documents: {rag.get_collection_stats().get('total_chunks', 0)} chunks indexed")
    print("\n📱 Frontend:")
    print("  • Expected at: http://localhost:3000")
    print("  • Make sure .env.local has: NEXT_PUBLIC_WS_URL=http://localhost:5001")
    
    if not rag:
        print("\n⚠️  WARNING: RAG not loaded!")
        print("  • Run: python ingest_docs.py --input data/manuals/")
        print("  • This is required for document-based suggestions")
    
    print("\n" + "=" * 80)
    print("🚀 Starting server...")
    print("=" * 80 + "\n")
    
    socketio.run(
        app,
        host='127.0.0.1',
        port=5001,
        debug=False,
        use_reloader=False,
        log_output=False,
        allow_unsafe_werkzeug=True
    )
