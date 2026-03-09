"""
Retrain EzaSmart RAG system with combined text vectorization.
Trains TF-IDF on both question and answer text for improved retrieval.
"""
import json
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
import datetime

chatbot_dir = Path(__file__).parent
wikipedia_path = chatbot_dir.parent / "wikipedia_hydro_knowledge.json"
stackex_path = chatbot_dir.parent / "hydro_qa_data.json"

print("=" * 70)
print("EzaSmart RAG Retraining")
print("=" * 70)

print("\nLoading knowledge sources...")
with open(wikipedia_path, 'r', encoding='utf-8') as f:
    wiki_data = json.load(f)
print(f"  Wikipedia: {len(wiki_data):,} entries")

with open(stackex_path, 'r', encoding='utf-8') as f:
    stackex_data = json.load(f)
print(f"  StackExchange: {len(stackex_data):,} entries")

all_questions = []
all_answers = []
all_sources = []

print("\nProcessing Wikipedia data...")
for entry in wiki_data:
    q = entry.get('instruction', '').strip()
    a = entry.get('response', '').strip()
    if q and a:
        all_questions.append(q)
        all_answers.append(a)
        all_sources.append(entry.get('source', 'Wikipedia'))

print("Processing StackExchange data...")
for entry in stackex_data:
    q = entry.get('question', '').strip()
    a = entry.get('response', '').strip()
    if q and a:
        all_questions.append(q)
        all_answers.append(a)
        all_sources.append('StackExchange')

print(f"\nTotal Q&A pairs: {len(all_questions):,}")
print(f"  Wikipedia: {len(wiki_data):,}")
print(f"  StackExchange: {len(stackex_data):,}")

print("\nCreating combined text documents...")
combined_texts = []
for q, a in zip(all_questions, all_answers):
    combined = f"{q} {a}"
    combined_texts.append(combined)

print(f"Combined {len(combined_texts):,} documents")

print("\nBuilding TF-IDF index...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english',
    lowercase=True,
    min_df=2
)

tfidf_matrix = vectorizer.fit_transform(combined_texts)
print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")
print(f"Vocabulary size: {len(vectorizer.vocabulary_):,} terms")

print("\nSaving model artifacts...")

with open(chatbot_dir / "tfidf_vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)
print("Saved tfidf_vectorizer.pkl")

with open(chatbot_dir / "tfidf_matrix.pkl", "wb") as f:
    pickle.dump(tfidf_matrix, f)
print("Saved tfidf_matrix.pkl")

kb = {
    'questions': all_questions,
    'answers': all_answers,
    'sources': all_sources
}
with open(chatbot_dir / "knowledge_base.pkl", "wb") as f:
    pickle.dump(kb, f)
print("Saved knowledge_base.pkl")

metadata = {
    "model_name": "Afsa20/Farmsmart_Growmate",
    "total_pairs": len(all_questions),
    "stackexchange_pairs": len(stackex_data),
    "wikipedia_pairs": len(wiki_data),
    "retrieval_threshold": 0.3,
    "tfidf_features": 5000,
    "created_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": "3.11.9",
    "fix_applied": "v2_combined_text_vectorization",
    "fix_description": "TF-IDF trained on combined question+answer text"
}

with open(chatbot_dir / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)
print("Updated metadata.json")

print("\n" + "=" * 70)
print("RAG system retrained successfully")
print("=" * 70)
print(f"\nTotal Q&A pairs: {len(all_questions):,}")
print(f"TF-IDF features: {tfidf_matrix.shape[1]:,}")
print("\nRestart the Flask app to use the updated model")