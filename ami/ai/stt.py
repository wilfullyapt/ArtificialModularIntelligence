"""Speech-to-text backends for AMI Listener (cloud or local)."""

from __future__ import annotations

import io
import os
from typing import Callable, Optional, Protocol


class SttBackend(Protocol):
    name: str

    def transcribe_wav(self, wav_bytes: bytes, sample_rate: int = 16000) -> str: ...


class GoogleSttBackend:
    """Legacy cloud path via SpeechRecognition + Google."""

    name = "google"

    def transcribe_wav(self, wav_bytes: bytes, sample_rate: int = 16000) -> str:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        audio = sr.AudioData(wav_bytes, sample_rate=sample_rate, sample_width=2)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            raise RuntimeError(f"Google STT request failed: {exc}") from exc


class FasterWhisperSttBackend:
    """Local STT via faster-whisper (optional dependency)."""

    name = "local"

    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "stt.backend=local requires faster-whisper. "
                "pip install faster-whisper  (or use stt.backend=google)"
            ) from exc
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        return self._model

    def transcribe_wav(self, wav_bytes: bytes, sample_rate: int = 16000) -> str:
        import tempfile
        from pathlib import Path

        model = self._load()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            path = Path(tmp.name)
        try:
            segments, _info = model.transcribe(str(path), language="en")
            text = " ".join(seg.text.strip() for seg in segments if seg.text).strip()
            return text
        finally:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


class CallableSttBackend:
    """Test double / injection seam."""

    name = "callable"

    def __init__(self, fn: Callable[[bytes, int], str]):
        self._fn = fn

    def transcribe_wav(self, wav_bytes: bytes, sample_rate: int = 16000) -> str:
        return self._fn(wav_bytes, sample_rate)


def resolve_stt_backend(
    backend: Optional[str] = None,
    *,
    model_size: str = "tiny",
    device: str = "cpu",
) -> SttBackend:
    """
    Resolve STT backend from explicit name or env AMI_STT_BACKEND.

    Values: local | google | (default: local if AMI_STT_BACKEND unset prefers local,
    but falls back to google only when explicitly set).
    Product default in config_template: local.
    """
    name = (backend or os.environ.get("AMI_STT_BACKEND") or "local").strip().lower()
    if name in ("local", "whisper", "faster-whisper", "faster_whisper"):
        return FasterWhisperSttBackend(model_size=model_size, device=device)
    if name in ("google", "cloud"):
        return GoogleSttBackend()
    raise ValueError(f"Unknown STT backend: {name!r} (use local or google)")


def wav_bytes_from_pcm16(pcm: bytes, sample_rate: int = 16000) -> bytes:
    """Wrap raw s16le mono PCM in a minimal WAV container."""
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()
