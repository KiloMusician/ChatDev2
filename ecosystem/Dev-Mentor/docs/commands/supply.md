# supply

## NAME
supply — manage colony supply chains between controlled nodes

## SYNOPSIS
```
supply chain <from_node> <to_node>
supply status
supply break <from_node> <to_node>
```

## DESCRIPTION
Create resource flows between claimed nodes. Each active supply chain adds +5 compute units/hr to your resource dashboard. Requires both endpoints to be claimed.

## SUBCOMMANDS
- `supply chain <from> <to>` — establish a supply chain between two claimed nodes
- `supply status` — view all active chains and per-chain resource rates
- `supply break <from> <to>` — dismantle an existing supply chain

## SEE ALSO
`resources`, `nodes`, `colonize`, `defend`
