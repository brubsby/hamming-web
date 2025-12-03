import argparse
import string
import requests
import os
import sys
import json
import networkx as nx
from networkx.readwrite import json_graph
from collections import deque

WORDS_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
NAMES_URL = "https://raw.githubusercontent.com/dominictarr/random-name/master/first-names.txt"

CACHE_DIR = ".cache"
WORDS_FILE = os.path.join(CACHE_DIR, "words.txt")
NAMES_FILE = os.path.join(CACHE_DIR, "names.txt")

def download_file(url, dest):
    if os.path.exists(dest):
        return
    print(f"Downloading {url} to {dest}...")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(response.text)

def load_words():
    download_file(WORDS_URL, WORDS_FILE)
    download_file(NAMES_URL, NAMES_FILE)
    
    valid_words = set()
    
    with open(WORDS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            valid_words.add(line.strip().lower())
            
    with open(NAMES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            valid_words.add(line.strip().lower())
            
    return valid_words

def is_valid_phrase(phrase, valid_words):
    # Split by whitespace and check each part
    parts = phrase.split()
    if not parts:
        return False
    for part in parts:
        if part.lower() not in valid_words:
            return False
    return True

def normalize_phrase(phrase):
    """Enforce every word to have an uppercase first letter, and the rest lowercase."""
    return ' '.join(w.capitalize() for w in phrase.split())

def get_neighbors(phrase, valid_words):
    # Work with lowercase for generation logic to avoid case duplicates
    lower_phrase = phrase.lower()
    neighbors = set()
    
    # Only use lowercase letters for mutations. 
    # We normalize the result to Title Case, so 'a' and 'A' result in the same output.
    alphabet = string.ascii_lowercase
    
    # 1. Deletions
    for i in range(len(lower_phrase)):
        candidate = lower_phrase[:i] + lower_phrase[i+1:]
        if is_valid_phrase(candidate, valid_words):
            neighbors.add(normalize_phrase(candidate))
            
    # 2. Substitutions
    for i in range(len(lower_phrase)):
        if lower_phrase[i] == ' ':
            continue
        
        original_char = lower_phrase[i]
        for char in alphabet:
            if char == original_char:
                continue
            candidate = lower_phrase[:i] + char + lower_phrase[i+1:]
            if is_valid_phrase(candidate, valid_words):
                neighbors.add(normalize_phrase(candidate))
                
    # 3. Insertions
    for i in range(len(lower_phrase) + 1):
        for char in alphabet:
            candidate = lower_phrase[:i] + char + lower_phrase[i:]
            if is_valid_phrase(candidate, valid_words):
                neighbors.add(normalize_phrase(candidate))
    
    # Remove self-loops if any
    normalized_start = normalize_phrase(phrase)
    if normalized_start in neighbors:
        neighbors.remove(normalized_start)
        
    return neighbors

def generate_graph(start_phrase, depth):
    print("Loading word lists...")
    valid_words = load_words()
    print(f"Loaded {len(valid_words)} unique words/names.")
    
    # Normalize start phrase immediately
    start_phrase = normalize_phrase(start_phrase)

    if not is_valid_phrase(start_phrase, valid_words):
        print(f"Warning: Start phrase '{start_phrase}' contains words not in the dictionary.")

    G = nx.DiGraph()
    G.add_node(start_phrase)
    
    queue = deque([(start_phrase, 0)])
    visited = {start_phrase: 0}
    
    print(f"Generating graph for '{start_phrase}' with depth {depth}...")
    
    while queue:
        current_phrase, current_depth = queue.popleft()
        
        if current_depth >= depth:
            continue
        
        neighbors = get_neighbors(current_phrase, valid_words)
        for neighbor in neighbors:
            if neighbor not in visited:
                visited[neighbor] = current_depth + 1
                queue.append((neighbor, current_depth + 1))
                G.add_edge(current_phrase, neighbor)
            elif visited[neighbor] == current_depth + 1:
                G.add_edge(current_phrase, neighbor)
            
    return G

def main():
    parser = argparse.ArgumentParser(description="Generate a graph of phrase neighbors.")
    parser.add_argument("phrase", type=str, help="The starting string/phrase.")
    parser.add_argument("--depth", type=int, default=1, help="Depth of search (default: 1).")
    parser.add_argument("--json", type=str, help="Path to save the graph as a JSON file for visualization.")
    
    args = parser.parse_args()
    
    G = generate_graph(args.phrase, args.depth)
    
    print(f"\nGraph generated with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    if args.json:
        data = json_graph.node_link_data(G)
        with open(args.json, 'w') as f:
            json.dump(data, f)
        print(f"Graph data saved to {args.json}")
    else:
        print("Edges:")
        for u, v in G.edges():
            print(f"  {u} -> {v}")

if __name__ == "__main__":
    main()
