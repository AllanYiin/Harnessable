# ToolAnything Gateway Contract

Stage 17 adds a provider-neutral `ExternalCapabilityContract` for function
tools, MCP descriptors, A2A agent cards, HTTP tools, provider adapters, sandbox
tools, and filesystem/resource adapters.

The contract is stored under:

```text
CapabilityProfile.contracts["external_capability"]
```

Older selectors and rules continue to read:

- `risk`
- `permissions`
- `approval`
- `fallback`
- `observability`

## Guarantees

- No real MCP or A2A network dependency is required in core.
- Gateway events expose the contract in event metadata and capability metadata.
- Missing high-risk metadata becomes explicit warnings.
- Fallback comparison can reject broader tenant, purpose, approval, data,
  network, destructive, and cost boundaries.

## Example

```python
from harnessable.capabilities import normalize_mcp_contract

contract = normalize_mcp_contract(
    {"name": "mcp.search", "inputSchema": {"type": "object"}},
    tenant_constraints={"allowed_tenant_ids": ["tenant_a"]},
    purpose_constraints={"allowed_purposes": ["support"]},
)
capability = contract.to_capability_profile()
```

## Verification

```bash
python -m pytest tests/test_external_capability_contract.py tests/test_gateways_and_adapters.py
```

