from dataclasses import dataclass
from typing import Dict, List, Optional
import re
from models.graph_state import FillStrategy
@dataclass
class FieldClassification:
    # ...existing code...
    fill_strategy: FillStrategy
