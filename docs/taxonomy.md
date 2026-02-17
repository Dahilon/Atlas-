# Taxonomy Mapping (v1)

We map GDELT events into a small number of analyst-friendly categories:

- Armed Conflict
- Civil Unrest
- Diplomacy / Sanctions
- Economic Disruption
- Infrastructure / Energy
- Crime / Terror

The mapping is implemented in `backend/app/taxonomy.py` as a pure function:

`map_event_to_category(event_code, quad_class, goldstein) -> category`

High-level rules (v1):

- **Armed Conflict**: EventCode prefixes `18*`, `19*`, `20*`
- **Civil Unrest**: EventCode prefix `14*` (protests, demonstrations)
- **Diplomacy / Sanctions**: EventCode prefixes `07*`, `08*`, `09*`
- **Economic Disruption**: EventCode prefixes `10*`, `11*`
- **Infrastructure / Energy**: specific `19x` codes associated with infrastructure
- **Crime / Terror**: EventCode prefix `17*`; also used as a fallback for conflict-like QuadClass values

QuadClass-based fallback:

- QuadClass in {3, 4} → `Crime / Terror`
- QuadClass in {1, 2} → `Diplomacy / Sanctions`

These rules are intentionally simple and will be refined in later iterations.

