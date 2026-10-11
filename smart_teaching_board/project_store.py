"""
Project Save/Load (.stb format) for Smart Teaching Board.
"""

import json
from typing import Dict, Any, Optional


class ProjectStore:
    @staticmethod
    def save_to_file(file_path: str, data: Dict[str, Any]) -> bool:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save project: {e}")
            return False

    @staticmethod
    def load_from_file(file_path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load project: {e}")
            return None
