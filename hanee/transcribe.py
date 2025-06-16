# transcribe.py
import sys
import whisper
import json

model = whisper.load_model("base")
result = model.transcribe(sys.argv[1], language='ko')
print(json.dumps({
    "text": result["text"],
    "segments": result.get("segments"),
    "language": result.get("language")
}))
