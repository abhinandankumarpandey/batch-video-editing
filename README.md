# batch-video-editing
A video editing automation 
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load model and tokenizer
model = AutoModelForSequenceClassification.from_pretrained("nayeems94/text-emotion-classifier")
tokenizer = AutoTokenizer.from_pretrained("nayeems94/text-emotion-classifier")

# Example text
text = "I am feeling so frustrated and angry!"

# Tokenize
inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)

# Predict
outputs = model(**inputs)
logits = outputs.logits
predicted_class_id = logits.argmax(dim=-1).item()

# Emotion labels
id2label = {
    0: 'admiration', 1: 'amusement', 2: 'anger', 3: 'annoyance', 4: 'approval', 5: 'caring',
    6: 'confusion', 7: 'curiosity', 8: 'desire', 9: 'disappointment', 10: 'disapproval',
    11: 'disgust', 12: 'embarrassment', 13: 'excitement', 14: 'fear', 15: 'gratitude',
    16: 'grief', 17: 'joy', 18: 'love', 19: 'nervousness', 20: 'optimism', 21: 'pride',
    22: 'realization', 23: 'relief', 24: 'remorse', 25: 'sadness', 26: 'surprise', 27: 'neutral'
}

print(f"Predicted emotion: {id2label[predicted_class_id]}")

# output 
# Predicted emotion: anger



import random
from pathlib import Path

import pysubs2
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# ── Configuration ────────────────────────────────────────────────────────────

# Paths
SRT_PATH       = "subtitles.srt"
MEME_BASE_DIR  = Path("folder")  # contains subfolders: "anger", "joy", etc.

# Display timing (in ms)
MAX_DISPLAY_MS = 2000            # never show a meme longer than 2 seconds
START_OFFSET_PCT = 0.1           # wait 10% into subtitle before showing

# Filters
MIN_WORDS     = 3                # skip lines with fewer words
CONF_THRESH   = 0.5              # require ≥50% confidence
DIFF_THRESHOLD = 0.06            # Δ threshold between top‑2 scores
SKIP_NEUTRAL  = True             # drop "neutral" predictions

# Model checkpoint
MODEL_NAME = "nayeems94/text-emotion-classifier"

# Mapping from label IDs to emotion names
LABEL_ID_TO_NAME = {
    0: "admiration", 1: "amusement", 2: "anger", 3: "annoyance", 4: "approval",
    5: "caring", 6: "confusion", 7: "curiosity", 8: "desire", 9: "disappointment",
    10: "disapproval", 11: "disgust", 12: "embarrassment", 13: "excitement",
    14: "fear", 15: "gratitude", 16: "grief", 17: "joy", 18: "love",
    19: "nervousness", 20: "optimism", 21: "pride", 22: "realization",
    23: "relief", 24: "remorse", 25: "sadness", 26: "surprise", 27: "neutral"
}

# ── Load model and pipeline ───────────────────────────────────────────────────

tokenizer  = AutoTokenizer.from_pretrained(MODEL_NAME)
model      = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
classifier = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    top_k=None,                 # return all 28 scores
    function_to_apply="sigmoid" # multi‑label sigmoid scores
)

# ── Helper: choose final emotion via Δ-threshold ─────────────────────────────

def select_emotion(scores: dict) -> (str, float):
    """
    Given a dict emotion->score, sort descending,
    compute Δ between top two, and return:
      (chosen_emotion, chosen_confidence)
    """
    sorted_emos = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    (e1, s1), (e2, s2) = sorted_emos[0], sorted_emos[1]
    if (s1 - s2) > DIFF_THRESHOLD:
        return e1, s1
    else:
        return e2, s2

# ── Build the timeline dicts ─────────────────────────────────────────────────

# Load subtitles
subs = pysubs2.load(SRT_PATH)

timeline = []
for sub in subs:
    text = sub.text.strip()
    if not text:
        # skip empty lines
        continue

    # 1) Skip trivial lines by word count
    words = text.split()
    if len(words) < MIN_WORDS:
        continue

    # 2) Run classifier to get all emotion scores
    raw_out = classifier(text)[0]  # list of {label, score}
    scores = {}
    for item in raw_out:
        # extract numeric ID from "LABEL_17"
        idx = int(item["label"].split("_")[-1])
        emo = LABEL_ID_TO_NAME.get(idx, item["label"])
        scores[emo] = item["score"]

    # 3) Choose final emotion + confidence
    chosen_emo, conf = select_emotion(scores)

    # 4) Optionally skip neutral or low-confidence
    if (SKIP_NEUTRAL and chosen_emo == "neutral") or conf < CONF_THRESH:
        continue

    # 5) Pick a random meme PNG from the emotion folder
    emo_folder = MEME_BASE_DIR / chosen_emo
    pngs = list(emo_folder.glob("*.png"))
    if not pngs:
        # no memes for this emotion
        continue
    meme_file = random.choice(pngs)

    # 6) Compute when to show & hide
    duration = sub.end - sub.start                      # in ms
    start_ms = sub.start + int(duration * START_OFFSET_PCT)
    end_ms   = min(sub.end, start_ms + MAX_DISPLAY_MS)

    # 7) Append to the timeline list
    timeline.append({
        "subtitle_index": sub.index,
        "text":            text,
        "emotion":         chosen_emo,
        "confidence":      round(conf, 2),
        "meme_path":       str(meme_file),
        "start_ms":        start_ms,
        "end_ms":          end_ms
    })

# ── Example: print first few entries ─────────────────────────────────────────

if __name__ == "__main__":
    from pprint import pprint
    print(f"Generated {len(timeline)} meme-timeline entries.")
    pprint(timeline[:5])
