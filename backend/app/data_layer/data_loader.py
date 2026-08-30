import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings
from app.data_layer.models import (
    CallTranscript,
    CustomerProfile,
    KnowledgeBaseArticle,
    TenantAlias,
    Ticket,
)

logger = logging.getLogger("fleetpanda.dataloader")


class DataLoader:
    """
    Unified Data Loader that loads, indexes, and validates all JSON datasets:
    - customers.json
    - tenant_aliases.json
    - tickets.json
    - call_transcripts.json
    - knowledge_base.json
    """
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.customers: Dict[int, CustomerProfile] = {}
        self.aliases: List[TenantAlias] = []
        self.tickets: List[Ticket] = []
        self.transcripts: List[CallTranscript] = []
        self.kb_articles: List[KnowledgeBaseArticle] = []
        self._load_all_data()

    def _load_all_data(self):
        """Loads and indexes all JSON dataset files."""
        # 1. Customers
        cust_path = self.data_dir / "customers.json"
        if cust_path.exists():
            with open(cust_path, "r", encoding="utf-8") as f:
                raw_cust = json.load(f)
                for item in raw_cust:
                    cust = CustomerProfile(**item)
                    self.customers[cust.tenant_id] = cust
            logger.info(f"Loaded {len(self.customers)} customer profiles.")
        else:
            logger.warning(f"File not found: {cust_path}")

        # 2. Tenant Aliases
        alias_path = self.data_dir / "tenant_aliases.json"
        if alias_path.exists():
            with open(alias_path, "r", encoding="utf-8") as f:
                raw_alias = json.load(f)
                for item in raw_alias:
                    self.aliases.append(TenantAlias(**item))
            logger.info(f"Loaded {len(self.aliases)} tenant aliases.")
        else:
            logger.warning(f"File not found: {alias_path}")

        # 3. Tickets
        tickets_path = self.data_dir / "tickets.json"
        if tickets_path.exists():
            with open(tickets_path, "r", encoding="utf-8") as f:
                raw_tickets = json.load(f)
                for item in raw_tickets:
                    self.tickets.append(Ticket(**item))
            logger.info(f"Loaded {len(self.tickets)} support tickets.")
        else:
            logger.warning(f"File not found: {tickets_path}")

        # 4. Call Transcripts
        trans_path = self.data_dir / "call_transcripts.json"
        if trans_path.exists():
            with open(trans_path, "r", encoding="utf-8") as f:
                raw_trans = json.load(f)
                for item in raw_trans:
                    self.transcripts.append(CallTranscript(**item))
            logger.info(f"Loaded {len(self.transcripts)} call transcripts.")
        else:
            logger.warning(f"File not found: {trans_path}")

        # 5. Knowledge Base
        kb_path = self.data_dir / "knowledge_base.json"
        if kb_path.exists():
            with open(kb_path, "r", encoding="utf-8") as f:
                raw_kb = json.load(f)
                for item in raw_kb:
                    self.kb_articles.append(KnowledgeBaseArticle(**item))
            logger.info(f"Loaded {len(self.kb_articles)} knowledge base articles.")
        else:
            logger.warning(f"File not found: {kb_path}")

    def get_customer(self, tenant_id: int) -> Optional[CustomerProfile]:
        """Get customer profile by tenant_id."""
        return self.customers.get(tenant_id)

    def get_all_customers(self) -> List[CustomerProfile]:
        """Get list of all customer profiles."""
        return list(self.customers.values())

    def get_tickets_by_tenant(self, tenant_id: int) -> List[Ticket]:
        """Get all tickets submitted by a specific tenant."""
        return [t for t in self.tickets if t.tenant_id == tenant_id]

    def get_ticket_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Get ticket by ticket_id."""
        for t in self.tickets:
            if t.ticket_id == ticket_id:
                return t
        return None

    def get_transcripts_by_tenant_id(self, tenant_id: int, resolved_names: List[str]) -> List[CallTranscript]:
        """Get call transcripts matching resolved tenant names."""
        names_lower = {n.lower() for n in resolved_names}
        results = []
        for call in self.transcripts:
            if call.tenant_name.lower() in names_lower or call.resolved_tenant_id == tenant_id:
                results.append(call)
        return results

    def get_kb_articles_by_area(self, product_area: str) -> List[KnowledgeBaseArticle]:
        """Get KB articles matching product area."""
        return [kb for kb in self.kb_articles if kb.product_area == product_area]


data_loader = DataLoader()

