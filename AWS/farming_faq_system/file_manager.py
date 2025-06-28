import os
import json
import csv
import sqlite3
from datetime import datetime
import shutil
from pathlib import Path

class FAQFileManager:
    def __init__(self, base_dir="faq_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)  # Create directory if it doesn't exist
    
    def save_faq_to_json(self, question, answer, filename="faq.json"):
        data = {"question": question, "answer": answer, "timestamp": datetime.now().isoformat()}
        filepath = self.base_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_faq_from_json(self, filename="faq.json"):
        filepath = self.base_dir / filename
        if not filepath.exists():
            return None
        with open(filepath, 'r') as f:
            return json.load(f)
    
    # Add other methods (e.g., for CSV/SQLite) here
    def save_faq_to_csv(self, question, answer, filename="faq.csv"):
        filepath = self.base_dir / filename
        with open(filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), question, answer])
    
    def close(self):
        pass  # Optional cleanup
