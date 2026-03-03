import json
import requests
from typing import List, Dict
from bs4 import BeautifulSoup
import re

ARTICLES = [
    'Hydroponics',
    'Nutrient_film_technique',
    'Deep_water_culture',
    'Aeroponics',
    'Aquaponics',
    'Grow_light',
    'pH',
    'Electrical_conductivity',
    'Plant_nutrition',
    'Growing_medium',
    'Solution_culture',
    'Fertilizer',
    'Lettuce',
    'Tomato',
    'Greenhouse',
    'Vertical_farming',
]

def clean_text(text: str) -> str:
    text = ' '.join(text.split())
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\([^)]*\bsee also\b[^)]*\)', '', text, flags=re.IGNORECASE)
    return text.strip()

def fetch_wikipedia_article(title: str) -> Dict:
    print(f"Fetching: {title.replace('_', ' ')}")
    
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text|sections",
        "disabletoc": 1
    }
    
    headers = {
        'User-Agent': 'FarmSmartBot/1.0 (Educational hydroponics research; afsa.hydro@example.com)'
    }
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        if not response.text:
            print(f"Empty response from Wikipedia API")
            return None
        
        try:
            data = response.json()
        except json.JSONDecodeError as je:
            print(f"Invalid JSON response from Wikipedia")
            print(f"Response preview: {response.text[:300]}")
            return None
        
        if 'error' in data:
            print(f"Error: {data['error'].get('info', 'Unknown error')}")
            return None
        
        html_content = data['parse']['text']['*']
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for element in soup.select('table, .infobox, .navbox, .vertical-navbox, sup.reference, style, script'):
            element.decompose()
        
        paragraphs = []
        for p in soup.find_all('p'):
            text = clean_text(p.get_text())
            if len(text) > 50:
                paragraphs.append(text)
        
        if not paragraphs:
            print(f"No content extracted (found {len(soup.find_all('p'))} paragraphs total)")
            return None
        
        print(f"Extracted {len(paragraphs)} paragraphs")
        
        return {
            'title': title.replace('_', ' '),
            'url': f"https://en.wikipedia.org/wiki/{title}",
            'paragraphs': paragraphs
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except KeyError as e:
        print(f"Missing expected data in response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        return None

def split_into_chunks(article: Dict, max_chars: int = 500) -> List[Dict]:
    chunks = []
    
    for para in article['paragraphs']:
        if len(para) <= max_chars:
            chunks.append({
                'topic': article['title'],
                'content': para,
                'source': article['url']
            })
        else:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_len = len(sentence)
                
                if current_length + sentence_len > max_chars and current_chunk:
                    chunks.append({
                        'topic': article['title'],
                        'content': ' '.join(current_chunk),
                        'source': article['url']
                    })
                    current_chunk = [sentence]
                    current_length = sentence_len
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_len
            
            if current_chunk:
                chunks.append({
                    'topic': article['title'],
                    'content': ' '.join(current_chunk),
                    'source': article['url']
                })
    
    return chunks

def create_qa_pairs(chunks: List[Dict]) -> List[Dict]:
    qa_pairs = []
    
    for idx, chunk in enumerate(chunks):
        topic = chunk['topic']
        content = chunk['content']
        
        if 'Hydroponics' in topic and idx == 0:
            question = "What is hydroponics?"
        elif 'Nutrient film technique' in topic:
            question = f"Explain the nutrient film technique in hydroponics."
        elif 'Deep water culture' in topic:
            question = f"What is deep water culture (DWC) in hydroponics?"
        elif 'pH' in topic:
            question = f"What is pH and why is it important?"
        elif 'Electrical conductivity' in topic:
            question = f"What is electrical conductivity (EC) in hydroponics?"
        elif 'Nutrient' in topic or 'Fertilizer' in topic:
            question = f"Tell me about nutrients in hydroponics."
        elif 'Lettuce' in topic or 'Tomato' in topic:
            question = f"How do you grow {topic.lower()} hydroponically?"
        else:
            question = f"What should I know about {topic.lower()} in hydroponics?"
        
        qa_pairs.append({
            'instruction': question,
            'response': content,
            'source': chunk['source'],
            'topic': topic
        })
    
    return qa_pairs

print(f"Wikipedia Hydroponics Knowledge Scraper")
print(f"Articles to fetch: {len(ARTICLES)}")

all_chunks = []
article_stats = {}

for article_title in ARTICLES:
    article = fetch_wikipedia_article(article_title)
    
    if article:
        chunks = split_into_chunks(article, max_chars=600)
        all_chunks.extend(chunks)
        article_stats[article['title']] = len(chunks)
    else:
        article_stats[article_title.replace('_', ' ')] = 0

print(f"\nCreating Q&A pairs...")
qa_dataset = create_qa_pairs(all_chunks)

# Save to file
output_file = 'Models/wikipedia_hydro_knowledge.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(qa_dataset, f, indent=4, ensure_ascii=False)

print(f"\nScraping complete")
print(f"Total knowledge chunks: {len(all_chunks)}")
print(f"Q&A pairs created: {len(qa_dataset)}")
print(f"Saved to: {output_file}")
print(f"\nBreakdown by article:")
for article, count in sorted(article_stats.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"  {article:30s}: {count:3d} chunks")
