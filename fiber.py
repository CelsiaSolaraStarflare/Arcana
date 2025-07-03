import re
from typing import List, Dict
from datetime import datetime
from collections import Counter
import jieba  # For Chinese word segmentation
import csv
import ast  # For safely evaluating string representations of Python literals

class FiberDBMS:
    """
    A simple in-memory, file-backed search engine.
    It builds an inverted index for fast keyword-based retrieval and supports
    ranking, snippets, and dynamic tag updates.
    The database is persisted to a CSV file.
    """
    def __init__(self):
        self.database: List[Dict[str, str]] = []
        self.content_index: Dict[str, List[int]] = {}

    def is_empty(self) -> bool:
        """Checks if the database has any entries."""
        return not self.database

    def add_entry(self, name: str, content: str, tags: List[str]) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "name": name,
            "timestamp": timestamp,
            "content": content,
            "tags": ','.join(tags) if isinstance(tags, list) else tags
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
        with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['name', 'timestamp', 'content', 'tags'])
            for entry in self.database:
                writer.writerow([entry['name'], entry['timestamp'], entry['content'], entry['tags']])
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
        if re.search(r'[\u4e00-\u9fff]', text):
            return list(jieba.cut(text))
        else:
            return re.findall(r'\w+', text.lower())

    def _get_snippet(self, content: str, query_words: List[str], max_length: int = 200) -> str:
        content_tokens = self._tokenize(content)
        best_start = 0
        max_score = 0
        for i in range(max(1, len(content_tokens) - max_length)):
            snippet = content_tokens[i:i+max_length]
            score = sum(snippet.count(word) * (len(word) ** 0.5) for word in query_words)
            if score > max_score:
                max_score = score
                best_start = i
        snippet = ''.join(content_tokens[best_start:best_start+max_length])
        return snippet + "..." if len(content) > max_length else snippet

    def _update_tags(self, original_tags: str, content: str, query_words: List[str]) -> str:
        tags = original_tags.split(',') if original_tags else []
        original_tag = tags[0] if tags else ''
        words = self._tokenize(content)
        word_counts = Counter(words)
        relevant_keywords = [word for word in query_words if word in word_counts and word not in tags]
        relevant_keywords += [word for word, count in word_counts.most_common(5) if word not in tags and word not in query_words]
        updated_tags = [original_tag] + tags[1:] + relevant_keywords if original_tag else relevant_keywords
        return ','.join(updated_tags)

    def load_from_file(self, filename: str) -> None:
        self.database.clear()
        self.content_index.clear()
        with open(filename, 'r', encoding='utf-8', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for idx, row in enumerate(reader):
                try:
                    # Basic validation to ensure essential keys exist and are not None.
                    if not all(k in row and row[k] is not None for k in ['name', 'timestamp', 'content', 'tags']):
                        print(f"[X] Skipped malformed row (missing keys): {row}")
                        continue
                    
                    # Handle cases where tags are stored as a stringified list.
                    tags = row['tags']
                    if tags.startswith('[') and tags.endswith(']'):
                        try:
                            tags_list = ast.literal_eval(tags)
                            tags = ','.join(str(t).strip() for t in tags_list)
                        except (ValueError, SyntaxError):
                            # If literal_eval fails, keep the original string but log it.
                            print(f"[!] Could not parse tags: {tags}")
                    
                    entry = {
                        "name": row['name'],
                        "timestamp": row['timestamp'],
                        "content": row['content'],
                        "tags": tags
                    }
                    self.database.append(entry)
                    self._index_content(idx, entry['content'])
                except Exception as e:
                    print(f"[X] Skipped unreadable row: {row} (error: {e})")


def main():
    """
    A simple command-line interface for testing the FiberDBMS search functionality.
    """
    dbms = FiberDBMS()
    
    db_file = "arcana_index.csv"
    # Load or create the database
    dbms.load_or_create(db_file)

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
    dbms.save(db_file)

if __name__ == "__main__":
    main()
