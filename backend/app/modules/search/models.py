from pydantic import BaseModel


# All searchable entity labels in Gremlin
SEARCHABLE_LABELS: list[str] = [
    "Service",
    "AzureResource",
    "Environment",
    "Team",
    "ApiEndpoint",
    "Package",
    "Incident",
    "ADOWorkItem",
]

# Gremlin label → name property key (Incident/ADOWorkItem use "title")
NAME_PROPERTY: dict[str, str] = {
    "Service": "name",
    "AzureResource": "name",
    "Environment": "name",
    "Team": "name",
    "ApiEndpoint": "name",
    "Package": "name",
    "Incident": "title",
    "ADOWorkItem": "title",
}


class SearchHit(BaseModel):
    id: str
    entity_type: str
    name: str          # display name (resolved from name or title field)
    description: str = ""
    score: float = 1.0  # relevance (1.0 = name match, 0.5 = description match)
    tags: list[str] = []


class SearchResponse(BaseModel):
    query: str
    total: int
    hits: list[SearchHit]
