import json
from pathlib import Path

from table_sales_assistant.leads.models import Lead


class JSONLeadRepository:
    def __init__(self, leads_path: Path) -> None:
        self.leads_path = leads_path

    def _ensure_file(self) -> None:
        if not self.leads_path.exists():
            self.leads_path.parent.mkdir(parents=True, exist_ok=True)
            self.leads_path.write_text('[]', encoding='utf-8')

    def save(self, lead: Lead) -> None:
        self._ensure_file()
        raw = json.loads(self.leads_path.read_text(encoding='utf-8'))
        raw.append(lead.model_dump())
        self.leads_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
