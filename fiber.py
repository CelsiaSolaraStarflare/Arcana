import re
from typing import List, Dict
from datetime import datetime
from collections import Counter
import jieba  # For Chinese word segmentation

class FiberDBMS:
    def __init__(self):
        self.database: List[Dict[str, str]] = []
        self.content_index: Dict[str, List[int]] = {}

    def add_entry(self, name: str, content: str, tags: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "name": name,
            "timestamp": timestamp,
            "content": content,
            "tags": tags
        }
        self.database.append(entry)
        self._index_content(len(self.database) - 1, content)

    def _index_content(self, entry_index: int, content: str) -> None:
        words = self._tokenize(content)
        for word in words:
            if word not in self.content_index:
                self.content_index[word] = []
            self.content_index[word].append(entry_index)

    def load_or_create(self, filename: str) -> None:
        try:
            self.load_from_file(filename)
            print(f"Loaded {len(self.database)} entries from {filename}.")
        except FileNotFoundError:
            print(f"{filename} not found. Creating a new database.")

    def query(self, query: str, top_n: int) -> List[Dict[str, str]]:
        query_words = self._tokenize(query)
        matching_indices = set()
        for word in query_words:
            if word in self.content_index:
                matching_indices.update(self.content_index[word])
        
        sorted_results = sorted(
            matching_indices,
            key=lambda idx: self._rate_result(self.database[idx], query_words),
            reverse=True
        )
        
        results = []
        for idx in sorted_results[:top_n]:
            entry = self.database[idx]
            snippet = self._get_snippet(entry['content'], query_words)
            updated_tags = self._update_tags(entry['tags'], entry['content'], query_words)
            results.append({
                'name': entry['name'],
                'content': snippet,
                'tags': updated_tags,
                'index': idx
            })
        
        return results

    def save(self, filename: str) -> None:
        with open(filename, 'w', encoding='utf-8') as f:
            for entry in self.database:
                line = f"{entry['name']}\t{entry['timestamp']}\t{entry['content']}\t{entry['tags']}\n"
                f.write(line)
        print(f"Updated database saved to {filename}.")

    def _rate_result(self, entry: Dict[str, str], query_words: List[str]) -> float:
        content_tokens = self._tokenize(entry['content'])
        name_tokens = self._tokenize(entry['name'])
        tags = entry['tags'].split(',')
        
        unique_matches = sum(1 for word in set(query_words) if word in content_tokens)
        content_score = sum(content_tokens.count(word) for word in query_words)
        name_score = sum(3 for word in query_words if word in name_tokens)
        phrase_score = 5 if all(word in content_tokens for word in query_words) else 0
        unique_match_score = unique_matches * 10
        
        tag_score = sum(2 for tag in tags if any(word in self._tokenize(tag) for word in query_words))
        
        length_penalty = min(1, len(content_tokens) / 100)
        
        return (content_score + name_score + phrase_score + unique_match_score + tag_score) * length_penalty

    def _tokenize(self, text: str) -> List[str]:
        # Check if the text contains Chinese characters
        if re.search(r'[\u4e00-\u9fff]', text):
            return list(jieba.cut(text))
        else:
            return re.findall(r'\w+', text.lower())

    def _get_snippet(self, content: str, query_words: List[str], max_length: int = 200) -> str:
        content_tokens = self._tokenize(content)
        best_start = 0
        max_score = 0
        
        for i in range(len(content_tokens) - max_length):
            snippet = content_tokens[i:i+max_length]
            score = sum(snippet.count(word) * (len(word) ** 0.5) for word in query_words)
            if score > max_score:
                max_score = score
                best_start = i
        
        snippet = ''.join(content_tokens[best_start:best_start+max_length])
        return snippet + "..." if len(content) > max_length else snippet

    def _update_tags(self, original_tags: str, content: str, query_words: List[str]) -> str:
        tags = original_tags.split(',')
        original_tag = tags[0]  # Keep the first tag unchanged
        
        words = self._tokenize(content)
        word_counts = Counter(words)

        relevant_keywords = [word for word in query_words if word in word_counts and word not in tags]
        relevant_keywords += [word for word, count in word_counts.most_common(5) if word not in tags and word not in query_words]

        updated_tags = [original_tag] + tags[1:] + relevant_keywords
        return ','.join(updated_tags)

    def load_from_file(self, filename: str) -> None:
        self.database.clear()
        self.content_index.clear()
        with open(filename, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                name, timestamp, content, tags = line.strip().split('\t')
                self.database.append({
                    "name": name,
                    "timestamp": timestamp,
                    "content": content,
                    "tags": tags
                })
                self._index_content(idx, content)

def main():
    dbms = FiberDBMS()
    
    # Load or create the database
    dbms.load_or_create("Celsiaaa.txt")

    while True:
        query = input("\nEnter your search query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
        
        try:
            top_n = int(input("Enter the number of top results to display: "))
        except ValueError:
            print("Invalid input. Using default value of 5.")
            top_n = 5

        results = dbms.query(query, top_n)
        if results:
            print(f"\nTop {len(results)} results for '{query}':")
            for idx, result in enumerate(results, 1):
                print(f"\nResult {idx}:")
                print(f"Name: {result['name']}")
                print(f"Content: {result['content']}")
                print(f"Tags: {result['tags']}")
        else:
            print(f"No results found for '{query}'.")

    # Save updated database with new tags
    dbms.save("Celsiaaa.txt")

if __name__ == "__main__":
    main()
