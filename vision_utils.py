# vision_utils.py
import os
from google.cloud import vision
from google.oauth2 import service_account
from difflib import SequenceMatcher
import os
import re
import uuid
from typing import List, Tuple, Dict
from usage_tracker import is_limit_reached, increment_usage

#GOOGLE_CREDENTIALS_PATH = "western-mix-460602-k1-2e0681bf2697.json"
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
PHOTO_DIR = "photos"

os.makedirs(PHOTO_DIR, exist_ok=True)

credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)


def detect_text(image_path: str) -> str:
    if is_limit_reached():
        raise Exception("Превышен месячный лимит использования Google Vision API (1000 запросов)")
    
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations
    detected_text = texts[0].description if texts else ""

    increment_usage()  # Увеличиваем счётчик
    return detected_text


def aggressive_normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_words(text: str, min_length: int = 3) -> List[str]:
    normalized = aggressive_normalize(text)
    words = normalized.split()
    meaningful_words = [word for word in words if len(word) >= min_length and not word.isdigit()]
    return meaningful_words


def fuzzy_match_words(word1: str, word2: str, threshold: float = 0.8) -> bool:
    if not word1 or not word2:
        return False
    if word1 == word2:
        return True
    length_diff = abs(len(word1) - len(word2))
    max_length = max(len(word1), len(word2))
    if length_diff > max_length * 0.4:
        return False
    similarity = SequenceMatcher(None, word1, word2).ratio()
    return similarity >= threshold


def calculate_text_similarity(text1: str, text2: str) -> float:
    words1 = extract_words(text1)
    words2 = extract_words(text2)
    if not words1 and not words2:
        return 100.0
    if not words1 or not words2:
        return 0.0
    matched_words1 = set()
    matched_words2 = set()
    for i, word1 in enumerate(words1):
        for j, word2 in enumerate(words2):
            if j not in matched_words2 and fuzzy_match_words(word1, word2):
                matched_words1.add(i)
                matched_words2.add(j)
                break
    total_words = len(words1) + len(words2)
    matched_pairs = len(matched_words1)
    if total_words == 0:
        return 100.0
    similarity = (matched_pairs * 2) / total_words * 100
    return min(100.0, max(0.0, similarity))


def find_line_differences(reference_lines: List[str], compare_lines: List[str]) -> Dict:
    """
    Ищет различия, принимая reference_lines как эталон.
    Возвращает словарь с тремя списками:
        - deleted — удаленные строки
        - modified — измененные строки
        - added — добавленные строки
    """
    deleted = []
    modified = []
    used_compare_indices = set()

    # Проверяем каждую строку эталона
    for ref_idx, ref_line in enumerate(reference_lines):
        norm_ref = aggressive_normalize(ref_line)
        if not norm_ref:
            continue

        best_match_idx = -1
        best_similarity = 0
        best_line = ""

        # Ищем наиболее подходящее совпадение
        for cmp_idx, cmp_line in enumerate(compare_lines):
            if cmp_idx in used_compare_indices:
                continue
            norm_cmp = aggressive_normalize(cmp_line)
            if not norm_cmp:
                continue
            similarity = SequenceMatcher(None, norm_ref, norm_cmp).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_idx = cmp_idx
                best_line = cmp_line

        if best_match_idx != -1:
            used_compare_indices.add(best_match_idx)
            if best_similarity < 0.98:
                modified.append({
                    'old': ref_line,
                    'new': best_line,
                    'similarity': best_similarity * 100
                })
        else:
            deleted.append({'old': ref_line})

    # Оставшиеся строки в compare_lines — это добавленные
    added = [{'new': line} for idx, line in enumerate(compare_lines) if idx not in used_compare_indices]

    return {
        'deleted': deleted,
        'modified': modified,
        'added': added
    }