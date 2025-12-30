"""
LumenOrb v2.0 - Design Feedback System
Captures successful designs for few-shot learning and future fine-tuning
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any


class DesignFeedback:
    """
    System to capture and retrieve successful designs.
    
    Features:
    - Save designs with ratings and notes
    - Retrieve examples for few-shot learning
    - Export training data for fine-tuning
    - Track design categories and success patterns
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the feedback system.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or Path("data/designs.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        print(f"✅ Design feedback database initialized: {self.db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main designs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS designs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt TEXT NOT NULL,
                    strategy TEXT,
                    recipe_json TEXT NOT NULL,
                    rating INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    parent_id INTEGER,
                    description TEXT,
                    FOREIGN KEY (parent_id) REFERENCES categories(id)
                )
            """)
            
            # Design-category relationship
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS design_categories (
                    design_id INTEGER,
                    category_id INTEGER,
                    PRIMARY KEY (design_id, category_id),
                    FOREIGN KEY (design_id) REFERENCES designs(id),
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)
            
            # Tags for quick filtering
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS design_tags (
                    design_id INTEGER,
                    tag_id INTEGER,
                    PRIMARY KEY (design_id, tag_id),
                    FOREIGN KEY (design_id) REFERENCES designs(id),
                    FOREIGN KEY (tag_id) REFERENCES tags(id)
                )
            """)
            
            # Insert default categories
            default_categories = [
                ("propulsion", None, "Rocket engines, nozzles, combustion chambers"),
                ("thermal", None, "Heat exchangers, cooling systems, heat sinks"),
                ("structural", None, "Load-bearing components, housings, frames"),
                ("filtration", None, "Filters, strainers, diffusers"),
                ("mechanical", None, "Gears, bearings, linkages"),
                ("connectors", None, "Flanges, joints, fastener patterns"),
            ]
            
            for name, parent, desc in default_categories:
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO categories (name, parent_id, description) VALUES (?, ?, ?)",
                        (name, parent, desc)
                    )
                except sqlite3.IntegrityError:
                    pass
            
            conn.commit()
    
    def save_design(self, prompt: str, recipe: Dict, 
                   rating: int = 0, notes: str = "",
                   strategy: str = "", categories: List[str] = None,
                   tags: List[str] = None) -> int:
        """
        Save a design to the database.
        
        Args:
            prompt: Original user prompt
            recipe: The generated recipe (dict or JSON string)
            rating: Quality rating (1-5 stars, 0 = unrated)
            notes: Optional notes about the design
            strategy: The engineer's strategy description
            categories: List of category names
            tags: List of tag names
            
        Returns:
            ID of the saved design
        """
        recipe_json = json.dumps(recipe) if isinstance(recipe, dict) else recipe
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert design
            cursor.execute("""
                INSERT INTO designs (prompt, strategy, recipe_json, rating, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (prompt, strategy, recipe_json, rating, notes))
            
            design_id = cursor.lastrowid
            
            # Add categories
            if categories:
                for cat_name in categories:
                    cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
                    row = cursor.fetchone()
                    if row:
                        cursor.execute(
                            "INSERT OR IGNORE INTO design_categories (design_id, category_id) VALUES (?, ?)",
                            (design_id, row[0])
                        )
            
            # Add tags
            if tags:
                for tag_name in tags:
                    # Create tag if not exists
                    cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                    tag_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT OR IGNORE INTO design_tags (design_id, tag_id) VALUES (?, ?)",
                        (design_id, tag_id)
                    )
            
            conn.commit()
            print(f"✅ Saved design #{design_id} with rating {rating}/5")
            return design_id
    
    def rate_design(self, design_id: int, rating: int, notes: str = None):
        """
        Update the rating for an existing design.
        
        Args:
            design_id: ID of the design to rate
            rating: New rating (1-5)
            notes: Optional updated notes
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if notes is not None:
                cursor.execute("""
                    UPDATE designs SET rating = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (rating, notes, design_id))
            else:
                cursor.execute("""
                    UPDATE designs SET rating = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (rating, design_id))
            
            conn.commit()
            print(f"✅ Updated design #{design_id} rating to {rating}/5")
    
    def get_examples(self, category: str = None, min_rating: int = 4,
                    limit: int = 3) -> List[Dict]:
        """
        Retrieve good examples for few-shot learning.
        
        Args:
            category: Optional category filter
            min_rating: Minimum rating to include
            limit: Maximum number of examples
            
        Returns:
            List of example designs
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if category:
                cursor.execute("""
                    SELECT d.* FROM designs d
                    JOIN design_categories dc ON d.id = dc.design_id
                    JOIN categories c ON dc.category_id = c.id
                    WHERE d.rating >= ? AND c.name = ?
                    ORDER BY d.rating DESC, d.created_at DESC
                    LIMIT ?
                """, (min_rating, category, limit))
            else:
                cursor.execute("""
                    SELECT * FROM designs
                    WHERE rating >= ?
                    ORDER BY rating DESC, created_at DESC
                    LIMIT ?
                """, (min_rating, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row['id'],
                    "prompt": row['prompt'],
                    "strategy": row['strategy'],
                    "recipe": json.loads(row['recipe_json']),
                    "rating": row['rating'],
                    "notes": row['notes']
                })
            
            return results
    
    def get_few_shot_prompt(self, category: str = None, n_examples: int = 2) -> str:
        """
        Generate a few-shot learning prompt with examples.
        
        Args:
            category: Optional category filter
            n_examples: Number of examples to include
            
        Returns:
            Formatted prompt string with examples
        """
        examples = self.get_examples(category=category, min_rating=4, limit=n_examples)
        
        if not examples:
            return ""
        
        lines = ["=== SUCCESSFUL DESIGN EXAMPLES ==="]
        
        for i, ex in enumerate(examples, 1):
            lines.append(f"\nExample {i} (Rating: {ex['rating']}/5)")
            lines.append(f"Prompt: {ex['prompt']}")
            if ex['strategy']:
                lines.append(f"Strategy: {ex['strategy'][:200]}...")
            lines.append(f"Recipe: {json.dumps(ex['recipe'], indent=2)[:500]}...")
            if ex['notes']:
                lines.append(f"Notes: {ex['notes']}")
        
        return "\n".join(lines)
    
    def export_training_data(self, output_path: Path, min_rating: int = 4) -> int:
        """
        Export designs as training data for fine-tuning.
        
        Args:
            output_path: Path to save JSONL file
            min_rating: Minimum rating to include
            
        Returns:
            Number of examples exported
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM designs WHERE rating >= ?
                ORDER BY rating DESC
            """, (min_rating,))
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            count = 0
            with open(output_path, 'w', encoding='utf-8') as f:
                for row in cursor.fetchall():
                    training_example = {
                        "messages": [
                            {"role": "user", "content": row['prompt']},
                            {"role": "assistant", "content": row['recipe_json']}
                        ],
                        "rating": row['rating']
                    }
                    f.write(json.dumps(training_example) + "\n")
                    count += 1
            
            print(f"✅ Exported {count} training examples to {output_path}")
            return count
    
    def get_stats(self) -> Dict:
        """Get statistics about saved designs."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM designs")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM designs WHERE rating >= 4")
            good = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(rating) FROM designs WHERE rating > 0")
            avg_rating = cursor.fetchone()[0] or 0
            
            cursor.execute("""
                SELECT c.name, COUNT(*) as count 
                FROM categories c
                JOIN design_categories dc ON c.id = dc.category_id
                GROUP BY c.name
                ORDER BY count DESC
            """)
            by_category = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                "total_designs": total,
                "good_designs": good,
                "average_rating": round(avg_rating, 2),
                "by_category": by_category
            }
    
    def list_recent(self, limit: int = 10) -> List[Dict]:
        """List recent designs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, prompt, rating, created_at
                FROM designs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
