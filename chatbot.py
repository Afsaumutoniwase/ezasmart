"""
EzaSmart RAG Chatbot - Retrieval-Augmented Generation for Hydroponics
Loads the trained RAG system and provides chat interface.
"""
import os
import pickle
import json
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import re

class EzaSmartChatbot:
    def __init__(self):
        self.rag_dir = Path(__file__).parent / "Models" / "chatbot"
        self.vectorizer = None
        self.tfidf_matrix = None
        self.questions = None
        self.answers = None
        self.sources = None
        self.metadata = None
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.threshold = 0.35  # Adjusted for combined text vectorization (was 0.4 originally, 0.3 temporarily)
        self.model_loaded = False
        self._load_system()
    
    def _load_system(self):
        """Load the RAG system components with fallback support."""
        try:
            print("Loading EzaSmart RAG Chatbot...")
            
            # Load TF-IDF vectorizer
            print("  • Loading TF-IDF vectorizer...")
            with open(self.rag_dir / "tfidf_vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)
            
            # Load TF-IDF matrix
            print("  • Loading TF-IDF matrix...")
            with open(self.rag_dir / "tfidf_matrix.pkl", "rb") as f:
                self.tfidf_matrix = pickle.load(f)
            
            # Load knowledge base
            print("  • Loading knowledge base...")
            with open(self.rag_dir / "knowledge_base.pkl", "rb") as f:
                kb = pickle.load(f)
                self.questions = kb['questions']
                self.answers = kb['answers']
                self.sources = kb['sources']
            
            # Load metadata
            print("  • Loading metadata...")
            with open(self.rag_dir / "metadata.json", "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            
            print(f"✓ Knowledge base loaded: {self.metadata['total_pairs']} Q&A pairs")
            
            # Try to load T5 model (optional - fallback to retrieval-only if fails)
            try:
                print("  • Loading T5 model (this may take a minute on first load)...")
                model_name = self.metadata.get('model_name', 'Afsa20/Farmsmart_Growmate')
                
                self.tokenizer = T5Tokenizer.from_pretrained(model_name)
                print("    ✓ Tokenizer loaded")
                
                self.model = T5ForConditionalGeneration.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if self.device.type == 'cuda' else torch.float32,
                    device_map="auto" if self.device.type == 'cuda' else None
                )
                print("    ✓ Model weights loaded")
                
                if self.device.type == 'cpu':
                    self.model = self.model.to(self.device)
                
                self.model.eval()
                self.model_loaded = True
                print(f"✓ T5 model ready on {self.device}")
                
            except RuntimeError as re:
                if "out of memory" in str(re).lower():
                    print(f"⚠ T5 Model load failed: OUT OF MEMORY")
                    print(f"  Available CUDA memory is insufficient. Using retrieval-only mode.")
                else:
                    print(f"⚠ T5 Model load failed: {re}")
                print("⚠ Running in retrieval-only mode (knowledge base answers only)")
                self.model_loaded = False
                
            except Exception as model_error:
                print(f"⚠ T5 Model load failed: {model_error}")
                print("⚠ Running in retrieval-only mode (knowledge base answers only)")
                self.model_loaded = False
            
            print("✓ EzaSmart Chatbot ready!")
            
        except Exception as e:
            print(f"✗ Critical error loading RAG system: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _normalize_user_query(self, query):
        """Normalize user input so retrieval/matching is explicitly case-insensitive."""
        if not query:
            return ""
        cleaned = re.sub(r'\s+', ' ', str(query)).strip()
        return cleaned.lower()
    
    def _classify_question_type(self, query):
        """
        Classify the type of question to help select better answers.
        Returns: 'definition', 'technical', 'history', 'problem', 'how_to', 'general'
        """
        query_lower = query.lower()
        
        # Definition questions
        if re.search(r'\b(what is|what are|define|definition of)\b', query_lower):
            # Check if it's asking for specs within a "what is" question
            if re.search(r'\b(ph|ec|temperature|ppm|optimal|best|ideal|range)\b', query_lower):
                return 'technical'
            return 'definition'
        
        # Technical/specification questions
        if re.search(r'\b(optimal|best|ideal|ph|ec|ppm|temperature|nutrient|concentration|level|range|value)\b', query_lower):
            return 'technical'
        
        # Historical questions
        if re.search(r'\b(history|historical|origin|ancient|developed|evolution|when did|past)\b', query_lower):
            return 'history'
        
        # Problem/troubleshooting questions
        if re.search(r'\b(problem|issue|disease|pest|trouble|wrong|fix|help|dying|yellow|brown|wilting)\b', query_lower):
            return 'problem'
        
        # How-to questions
        if re.search(r'\b(how to|how do|setup|build|grow|plant|start|maintain)\b', query_lower):
            return 'how_to'
        
        return 'general'
    
    def _score_answer_relevance(self, question, answer, query, question_type):
        """
        Score how well an answer matches the question type.
        Higher score = better match.
        """
        score = 0.0
        answer_lower = answer.lower()
        question_lower = question.lower()
        first_100 = answer_lower[:100]  # First 100 chars are most important
        first_200 = answer_lower[:200]
        
        if question_type == 'definition':
            # Strong preference for definitional language at the START of answer
            if re.search(r'^\w+\s+\(.*?\)\s+is\s+(a|an)', answer_lower[:80]):
                score += 0.8  # e.g., "The tomato (...) is a plant"
            elif re.search(r'^\w+\s+is\s+(a|an)', answer_lower[:50]):
                score += 0.7  # e.g., "Lettuce is an annual plant"
            elif re.search(r'\b(is a|is an|are|refers to|member of|type of)\b', first_100):
                score += 0.5
            
            # Prefer shorter, focused answers for definitions
            if len(answer) < 350:
                score += 0.3
            
            # Penalize answers that START with usage, problems, or technical details
            if re.search(r'^(small amounts|common|many|some|used for|cooking|pest)', first_100):
                score -= 0.5
            elif re.search(r'\b(pest|disease|problem|infection)\b', first_100):
                score -= 0.4
        
        elif question_type == 'technical':
            # Prefer answers with numbers, ranges, units
            if re.search(r'\d+\.?\d*\s*[-–]\s*\d+\.?\d*', answer_lower):
                score += 0.4
            if re.search(r'\b(ph|ec|ppm|temperature|°c|°f|range|level)\b', first_200):
                score += 0.3
        
        elif question_type == 'history':
            # Prefer answers with dates, time periods, historical context EARLY in text
            if re.search(r'\b(\d{3,4}\s*(bc|ad|bce|ce)?|ancient|origin|first\s+domest)', first_200):
                score += 0.7
            elif re.search(r'\b(century|early|developed|cultivated|history)', first_200):
               score += 0.4
            # Penalize if it's clearly NOT historical
            if re.search(r'\b(ph|ec|ppm|currently|today|2023|modern\s+production)\b', first_100):
                score -= 0.5
        
        elif question_type == 'problem':
            # Prefer answers about problems, diseases, troubleshooting
            if re.search(r'\b(pest|disease|problem|caused by|treatment|solution|prevent)\b', first_200):
                score += 0.5
        
        elif question_type == 'how_to':
            # Prefer procedural/instructional answers
            if re.search(r'\b(first|then|next|step|should|need to|can be|setup|procedure)\b', answer_lower):
                score += 0.3
        
        return score

    def _extract_definition_subject(self, query):
        """Extract the target concept from definition-style queries like 'what is hydroponics?'"""
        query_lower = query.lower().strip()
        patterns = [
            r'^what\s+is\s+(.+?)\??$',
            r'^what\s+are\s+(.+?)\??$',
            r'^define\s+(.+?)\??$',
            r'^definition\s+of\s+(.+?)\??$'
        ]
        for pattern in patterns:
            match = re.match(pattern, query_lower)
            if match:
                subject = re.sub(r'[^a-z0-9\s-]', ' ', match.group(1))
                subject = re.sub(r'\s+', ' ', subject).strip()
                return subject
        return None
    
    def _retrieve_answers(self, query, top_k=3):
        """
        Retrieve similar Q&A pairs from knowledge base using TF-IDF + question-type reranking.
        
        NOTE: The vectorizer is trained on combined question+answer text,
        so user queries can match on answer content, not just question keywords.
        """
        # Classify the question type
        question_type = self._classify_question_type(query)
        definition_subject = self._extract_definition_subject(query) if question_type == 'definition' else None

        # Fast-path exact definition lookup to avoid drifting to related-but-wrong entries.
        if definition_subject:
            normalized_subject = re.sub(r'\s+', ' ', definition_subject).strip().lower()
            target_forms = {
                f"what is {normalized_subject}",
                f"what are {normalized_subject}",
                f"define {normalized_subject}",
                f"definition of {normalized_subject}",
            }

            def normalize_question(text):
                cleaned = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
                return re.sub(r'\s+', ' ', cleaned).strip()

            exact_idx = None
            for i, q in enumerate(self.questions):
                normalized_q = normalize_question(q)
                if normalized_q in target_forms:
                    exact_idx = i
                    break

            if exact_idx is not None:
                results = [{
                    'score': 2.0,
                    'question': self.questions[exact_idx],
                    'answer': self.answers[exact_idx],
                    'source': self.sources[exact_idx]
                }]

                # Fill remaining slots with normal retrieval excluding the exact match.
                query_vec = self.vectorizer.transform([query])
                similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
                top_indices = np.argsort(similarities)[::-1]
                for idx in top_indices:
                    if idx == exact_idx:
                        continue
                    results.append({
                        'score': float(similarities[idx]),
                        'question': self.questions[idx],
                        'answer': self.answers[idx],
                        'source': self.sources[idx]
                    })
                    if len(results) >= top_k:
                        break
                return results
        
        # Get more candidates for reranking (3x top_k to have options)
        candidate_k = min(top_k * 3, len(self.questions))
        
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        top_indices = np.argsort(similarities)[::-1][:candidate_k]
        
        # Score each candidate with question-type awareness
        definition_subject = self._extract_definition_subject(query) if question_type == 'definition' else None
        candidates = []
        for idx in top_indices:
            tfidf_score = float(similarities[idx])
            relevance_score = self._score_answer_relevance(
                self.questions[idx], 
                self.answers[idx],
                query,
                question_type
            )
            subject_score = 0.0
            if definition_subject:
                q_lower = self.questions[idx].lower()
                a_lower = self.answers[idx].lower()
                a_start = a_lower[:120]

                # Strongly favor exact definition prompts for the requested concept.
                if re.search(rf'\bwhat\s+is\s+{re.escape(definition_subject)}\b', q_lower):
                    subject_score += 0.9
                elif definition_subject in q_lower:
                    subject_score += 0.45

                # Favor answers that define the exact concept near the beginning.
                if definition_subject in a_start:
                    subject_score += 0.25

                # Penalize discourse-heavy/non-definitional openings.
                if re.search(r'^(nevertheless|however|therefore|thus|in\s+contrast|for\s+example)', a_start):
                    subject_score -= 0.8

            # Combined score: 70% TF-IDF similarity, 30% question-type relevance
            combined_score = (0.7 * tfidf_score) + (0.3 * relevance_score) + subject_score
            
            candidates.append({
                'idx': idx,
                'tfidf_score': tfidf_score,
                'relevance_score': relevance_score,
                'subject_score': subject_score,
                'combined_score': combined_score,
                'question': self.questions[idx],
                'answer': self.answers[idx],
                'source': self.sources[idx]
            })
        
        # Re-rank by combined score
        candidates.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Return top_k after reranking
        results = []
        for candidate in candidates[:top_k]:
            results.append({
                'score': candidate['combined_score'],  # Use combined score
                'question': candidate['question'],
                'answer': candidate['answer'],
                'source': candidate['source']
            })
        
        return results
    
    def _generate_answer(self, question, max_length=150):
        """Generate answer using T5 model."""
        input_text = f"Answer this hydroponic farming question: {question}"
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                min_length=15,
                num_beams=4,
                early_stopping=True,
                repetition_penalty=1.2,  # Reduced from 2.5 - less aggressive
                no_repeat_ngram_size=3,
                temperature=0.3,  # Reduced from 0.7 - more conservative/factual
                top_p=0.75,  # Reduced from 0.9 - less randomness
                do_sample=True,  # Explicitly enable sampling for temperature
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def chat(self, question):
        """
        Main chat interface - hybrid RAG approach.
        Returns answer using retrieval if confidence is high, otherwise generates.
        Falls back to retrieval-only if T5 model not loaded.
        """
        if not question or not question.strip():
            return "Please ask a question about hydroponics!"

        normalized_question = self._normalize_user_query(question)
        
        # Retrieve similar Q&A pairs
        results = self._retrieve_answers(normalized_question, top_k=3)
        
        # Check if best match is above threshold
        if results and results[0]['score'] >= self.threshold:
            best = results[0]
            return best['answer']
        elif self.model_loaded:
            # Generate new answer with T5 if model is available
            try:
                return self._generate_answer(normalized_question)
            except Exception as e:
                print(f"Generation error: {e}")
                # Fallback to best retrieval result
                if results and results[0]['score'] > 0.2:
                    return results[0]['answer']
                else:
                    return "I don't have enough information to answer that question. Try asking about pH, EC, nutrients, or specific crops."
        else:
            # Model not loaded - use best retrieval result with disclaimer
            if results and results[0]['score'] > 0.2:
                return results[0]['answer']
            else:
                return "I don't have enough information to answer that specific question. Please try asking about:\n• pH and EC management\n• Nutrient solutions\n• Specific crops (lettuce, tomatoes, peppers)\n• System setup and troubleshooting"

# Singleton instance
_chatbot_instance = None

def get_chatbot():
    """Get or create chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = EzaSmartChatbot()
    return _chatbot_instance
