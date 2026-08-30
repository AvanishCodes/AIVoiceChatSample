import difflib
import re
from typing import Dict, List, Optional, Tuple

from app.data_layer.data_loader import data_loader

STOPWORDS = {
    "co", "company", "services", "service", "group", "petroleum", "petro", 
    "oil", "fuels", "fuel", "llc", "svcs", "gas", "energy", "solutions", 
    "distributors", "distributor", "inc", "corp", "corporation", "the"
}


def normalize_text(text: str) -> str:
    """Lowercase, strip non-alphanumeric chars, and remove noise stopwords."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    tokens = [w for w in cleaned.split() if w and w not in STOPWORDS]
    return " ".join(tokens)


class EntityResolver:
    """
    Multi-tiered Entity Resolver:
    Resolves tenant names, informal aliases, acronyms, and email domains to canonical tenant_id.
    """
    def __init__(self):
        self._build_indices()

    def _build_indices(self):
        """Build exact, alias, domain, and normalized lookup tables."""
        self.exact_map: Dict[str, int] = {}
        self.normalized_map: Dict[str, int] = {}
        self.email_domain_map: Dict[str, int] = {}
        self.tenant_all_names: Dict[int, List[str]] = {}

        # 1. Index canonical customer names
        for tenant_id, cust in data_loader.customers.items():
            self.exact_map[cust.name.lower()] = tenant_id
            norm = normalize_text(cust.name)
            if norm:
                self.normalized_map[norm] = tenant_id

            if tenant_id not in self.tenant_all_names:
                self.tenant_all_names[tenant_id] = []
            self.tenant_all_names[tenant_id].append(cust.name)

        # 2. Index aliases
        for alias_obj in data_loader.aliases:
            self.exact_map[alias_obj.alias.lower()] = alias_obj.tenant_id
            norm_alias = normalize_text(alias_obj.alias)
            if norm_alias:
                self.normalized_map[norm_alias] = alias_obj.tenant_id

            if alias_obj.tenant_id in self.tenant_all_names:
                self.tenant_all_names[alias_obj.tenant_id].append(alias_obj.alias)

        # 3. Index email domains from tickets
        for ticket in data_loader.tickets:
            if ticket.submitter_email and "@" in ticket.submitter_email:
                domain = ticket.submitter_email.split("@")[-1].lower()
                self.email_domain_map[domain] = ticket.tenant_id

        # Also register known company domains
        domain_defaults = {
            "cascadefuelservices.com": 1,
            "heartlandpropane.com": 2,
            "summitenergygroup.com": 3,
            "desertsunpetroleum.com": 4,
            "greatlakesfuel.com": 5,
            "pioneerfueldistributors.com": 6,
            "atlanticcoastenergy.com": 7,
            "timberridgeoil.com": 8,
            "prairiewindfuels.com": 9,
            "bayshorepetroleum.com": 10,
            "northernstarpropane.com": 11,
            "redwoodenergysolutions.com": 12,
        }
        self.email_domain_map.update(domain_defaults)

    def resolve_tenant(self, query: str) -> Optional[Tuple[int, str, float]]:
        """
        Resolves query string to (tenant_id, canonical_name, confidence).
        Returns None if no confident match is found.
        """
        if not query:
            return None

        query_str = query.strip()
        query_lower = query_str.lower()

        # Tier 1: Check for explicit "tenant 3", "tenant #4", "tenant_id: 2", "tenant_id 4"
        tenant_num_match = re.search(r"tenant(?:_id|\s*id)?\s*(?:#|:)?\s*(\d+)", query_lower)
        if tenant_num_match:
            tid = int(tenant_num_match.group(1))
            cust = data_loader.get_customer(tid)
            if cust:
                return (tid, cust.name, 1.0)

        # Tier 2: Check for email address or domain
        if "@" in query_lower:
            domain = query_lower.split("@")[-1].strip()
            if domain in self.email_domain_map:
                tid = self.email_domain_map[domain]
                cust = data_loader.get_customer(tid)
                if cust:
                    return (tid, cust.name, 0.99)

        if query_lower in self.email_domain_map:
            tid = self.email_domain_map[query_lower]
            cust = data_loader.get_customer(tid)
            if cust:
                return (tid, cust.name, 0.99)

        # Tier 3: Exact match against canonical names or aliases
        if query_lower in self.exact_map:
            tid = self.exact_map[query_lower]
            cust = data_loader.get_customer(tid)
            if cust:
                return (tid, cust.name, 1.0)

        # Tier 4: Normalized token match
        norm_query = normalize_text(query_str)
        if norm_query in self.normalized_map:
            tid = self.normalized_map[norm_query]
            cust = data_loader.get_customer(tid)
            if cust:
                return (tid, cust.name, 0.95)

        # Tier 5: Substring match in exact map
        for name_key, tid in self.exact_map.items():
            if len(name_key) > 3 and name_key in query_lower:
                cust = data_loader.get_customer(tid)
                if cust:
                    return (tid, cust.name, 0.90)

        # Tier 6: Fuzzy match using SequenceMatcher
        best_match_tid: Optional[int] = None
        best_score: float = 0.0

        for name_key, tid in self.exact_map.items():
            score = difflib.SequenceMatcher(None, query_lower, name_key).ratio()
            if score > best_score:
                best_score = score
                best_match_tid = tid

        # Check normalized fuzzy scores as well
        if norm_query:
            for norm_key, tid in self.normalized_map.items():
                score = difflib.SequenceMatcher(None, norm_query, norm_key).ratio()
                if score > best_score:
                    best_score = score
                    best_match_tid = tid

        if best_match_tid is not None and best_score >= 0.70:
            cust = data_loader.get_customer(best_match_tid)
            if cust:
                return (best_match_tid, cust.name, round(best_score, 2))

        return None

    def get_all_known_names_for_tenant(self, tenant_id: int) -> List[str]:
        """Returns all aliases and canonical names for a tenant."""
        return self.tenant_all_names.get(tenant_id, [])


entity_resolver = EntityResolver()
