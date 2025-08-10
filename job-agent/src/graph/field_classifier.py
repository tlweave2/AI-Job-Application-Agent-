from dataclasses import dataclass
from typing import Dict, List, Optional
import re

@dataclass
class FieldClassification:
    # ...existing code...
    fill_strategy: FillStrategy
