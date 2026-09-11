"""
Voice & Speech Provider Abstraction Layer
Provides modular interfaces for Speech-to-Text and Text-to-Speech with
browser-native HTML5 / Web Speech API bridges and text-first fallbacks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import re


class SpeechToTextProvider(ABC):
    """Abstract interface for transcribing audio to text."""

    @abstractmethod
    def transcribe(self, audio_data: Any) -> Dict[str, Any]:
        """Convert audio bytes/stream to text with observable speech metrics."""
        pass


class TextToSpeechProvider(ABC):
    """Abstract interface for synthesizing speech from text."""

    @abstractmethod
    def synthesize(self, text: str) -> Optional[bytes]:
        """Convert textual response to audio bytes."""
        pass


class WebSpeechBridgeProvider(SpeechToTextProvider):
    """
    Standard browser-native Web Speech API bridge provider.
    Runs locally in the user's browser without sending audio to third-party paid APIs.
    """

    def transcribe(self, audio_data: Any) -> Dict[str, Any]:
        transcript = str(audio_data or "").strip()
        metrics = analyze_observable_speech_metrics(transcript, duration_seconds=0.0)
        return {
            "transcript": transcript,
            "metrics": metrics,
            "provider": "web_speech_api"
        }


def analyze_observable_speech_metrics(transcript: str, duration_seconds: float = 0.0) -> Dict[str, Any]:
    """
    Compute strictly observable speech metrics (words, speaking pace, filler words).
    NEVER claims to measure psychological confidence or emotional state.
    """
    if not transcript:
        return {
            "word_count": 0,
            "duration_seconds": duration_seconds,
            "speaking_rate_wpm": 0.0,
            "filler_word_count": 0,
            "filler_words_detected": []
        }

    words = transcript.split()
    word_count = len(words)
    wpm = round((word_count / (duration_seconds / 60.0)), 1) if duration_seconds > 5 else 0.0

    filler_patterns = [r"\bumm?\b", r"\bahh?\b", r"\blike\b", r"\byou know\b", r"\bbasically\b", r"\bactually\b"]
    detected_fillers = []

    lower_text = transcript.lower()
    for pat in filler_patterns:
        matches = re.findall(pat, lower_text)
        if matches:
            detected_fillers.extend(matches)

    return {
        "word_count": word_count,
        "duration_seconds": round(duration_seconds, 1),
        "speaking_rate_wpm": wpm,
        "filler_word_count": len(detected_fillers),
        "filler_words_detected": list(set(detected_fillers))
    }


def get_web_speech_input_html(component_id: str = "voice_input_btn") -> str:
    """
    Generates a lightweight, sandboxed JavaScript snippet using the HTML5
    SpeechRecognition Web API to dictate answers into the active textarea.
    """
    return f"""
    <div style="margin: 8px 0 12px 0;">
        <button id="{component_id}" type="button" onclick="startDictation()" style="
            background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1;
            padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 600;
            cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
        ">
            🎤 Dictate Answer (Speech-to-Text)
        </button>
        <span id="{component_id}_status" style="font-size: 12px; color: #64748b; margin-left: 8px;"></span>
        
        <script>
        function startDictation() {{
            const status = document.getElementById('{component_id}_status');
            const btn = document.getElementById('{component_id}');
            
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
                status.innerText = "Browser does not support Web Speech API. Please type your answer.";
                return;
            }}
            
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRec();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            status.innerText = "🎙️ Listening... speak clearly into your mic.";
            btn.style.background = "#fee2e2";
            btn.style.borderColor = "#ef4444";
            
            recognition.onresult = function(event) {{
                const transcript = event.results[0][0].transcript;
                status.innerText = "✓ Transcribed! Review text box below.";
                btn.style.background = "#f1f5f9";
                btn.style.borderColor = "#cbd5e1";
                
                // Find nearest textarea in parent document
                const textareas = window.parent.document.querySelectorAll('textarea');
                if (textareas.length > 0) {{
                    const activeTa = textareas[textareas.length - 1];
                    const currentVal = activeTa.value ? activeTa.value + ' ' : '';
                    activeTa.value = currentVal + transcript;
                    activeTa.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }};
            
            recognition.onerror = function(event) {{
                status.innerText = "Mic error: " + event.error;
                btn.style.background = "#f1f5f9";
                btn.style.borderColor = "#cbd5e1";
            }};
            
            recognition.onend = function() {{
                btn.style.background = "#f1f5f9";
                btn.style.borderColor = "#cbd5e1";
            }};
            
            recognition.start();
        }}
        </script>
    </div>
    """
