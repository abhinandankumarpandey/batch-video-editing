import re
import os # Added os import
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch # PyTorch is a dependency of transformers

# --- Sentiment Analysis ---
SENTIMENT_MODEL_NAME = "nayeems94/text-emotion-classifier"
sentiment_tokenizer = None
sentiment_model = None
try:
    sentiment_tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_NAME)
    sentiment_model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_NAME)
    print(f"Sentiment analysis model '{SENTIMENT_MODEL_NAME}' loaded successfully.")
except Exception as e:
    print(f"Error loading sentiment model '{SENTIMENT_MODEL_NAME}': {e}")
    print("Sentiment analysis features will not be available.")

EMOTION_ID2LABEL = {
    0: 'admiration', 1: 'amusement', 2: 'anger', 3: 'annoyance', 4: 'approval',
    5: 'caring', 6: 'confusion', 7: 'curiosity', 8: 'desire', 9: 'disappointment',
    10: 'disapproval', 11: 'disgust', 12: 'embarrassment', 13: 'excitement',
    14: 'fear', 15: 'gratitude', 16: 'grief', 17: 'joy', 18: 'love',
    19: 'nervousness', 20: 'optimism', 21: 'pride', 22: 'realization',
    23: 'relief', 24: 'remorse', 25: 'sadness', 26: 'surprise', 27: 'neutral'
}
EMOTION_LABEL2ID = {v: k for k, v in EMOTION_ID2LABEL.items()}

def get_text_emotion(text):
    if not sentiment_tokenizer or not sentiment_model:
        return 'neutral', None

    try:
        inputs = sentiment_tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
        with torch.no_grad():
            outputs = sentiment_model(**inputs)
        logits = outputs.logits
        predicted_class_id = logits.argmax(dim=-1).item()
        return EMOTION_ID2LABEL.get(predicted_class_id, 'neutral'), logits
    except Exception as e:
        print(f"Error during sentiment analysis for text '{text[:50]}...': {e}")
        return 'neutral', None

# --- Subtitle Parsing (SRT) ---
def srt_time_to_seconds(srt_time_str):
    match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', srt_time_str)
    if match:
        h, m, s, ms = map(int, match.groups())
        return h * 3600 + m * 60 + s + ms / 1000.0
    return 0.0

def parse_srt_file(srt_file_path):
    if not os.path.exists(srt_file_path):
        print(f"SRT file not found: {srt_file_path}")
        return []
    subtitles = []
    try:
        with open(srt_file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        entry_pattern = re.compile(r'(\d+)\s*
(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*
((?:.+
?)+)', re.MULTILINE)
        for match in entry_pattern.finditer(content):
            start_time_str = match.group(2)
            end_time_str = match.group(3)
            text_lines = match.group(4).strip().split('
')
            text = " ".join(line.strip() for line in text_lines if line.strip())
            if text:
                subtitles.append({
                    'start': srt_time_to_seconds(start_time_str),
                    'end': srt_time_to_seconds(end_time_str),
                    'text': text
                })
    except Exception as e:
        print(f"Error parsing SRT file {srt_file_path}: {e}")
        return []
    return subtitles

if __name__ == '__main__':
    print("--- Testing utils.py ---")
    test_text_happy = "I am so happy and excited about this!"
    emotion_happy, _ = get_text_emotion(test_text_happy)
    print(f"Text: '{test_text_happy}' -> Emotion: {emotion_happy}")
    # assert emotion_happy in ['joy', 'excitement', 'optimism', 'admiration'], f"Emotion for happy text was {emotion_happy}"

    dummy_srt_content = "1\n00:00:01,000 --> 00:00:03,500\nThis is the first subtitle.\nIt has two lines.\n\n2\n00:00:04,100 --> 00:00:05,200\nSecond subtitle here."
    dummy_srt_path = "./dummy_test.srt"
    with open(dummy_srt_path, "w", encoding="utf-8") as f:
        f.write(dummy_srt_content)
    parsed_subs = parse_srt_file(dummy_srt_path)
    print(f"Parsed SRT ({dummy_srt_path}): Found {len(parsed_subs)} entries.")
    # assert len(parsed_subs) == 2, "SRT parsing incorrect entry count"
    os.remove(dummy_srt_path)
    print("--- utils.py tests finished ---")
