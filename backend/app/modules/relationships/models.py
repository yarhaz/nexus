from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field
import uuid


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Valid relationship types between entities
RelationshipType = Literal[
    "depends_on",
    "owned_by",
    "deployed_to",
    "exposes",
    "consumes",
    "causes",
    "fixes",
    "part_of",
    "monitors",
]


class EdgeCreate(BaseModel):
    source_id: str
    source_label: str
    target_id: str
    target_label: str
    relationship_type: RelationshipType
    properties: dict = {}


class EdgeEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    source_label: str
    target_id: str
    target_label: str
    relationship_type: str
    properties: dict = {}
    created_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


class GraphNode(BaseModel):
    id: str
    label: str
    name: str
    entity_type: str


class GraphEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    relationship_type: str


class EntityGraph(BaseModel):
    """Subgraph centred on a given entity (up to 2 hops)."""
    root_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
