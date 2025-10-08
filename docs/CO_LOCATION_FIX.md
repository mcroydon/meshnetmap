# Co-located Nodes Fix

## Problem

When collecting topology data via Bluetooth from a Meshtastic node, the system often has two nodes at the same physical location:

1. **Collection source node** (`hopsAway: -1`, `snr: null`) - The device we're connected to via Bluetooth
2. **Collection node** (`hopsAway: 0`) - The node that reports the network topology

In your case:
- **"Cool 🫘"** - Collection source (hopsAway: -1, no SNR)
- **"Cedar Park 🦙"** - Collection node (hopsAway: 0, SNR: 7.5)
- Both share GPS coordinates: `(30.4873, -97.8584)`

The original inference script didn't create connections between them because:
- "Cool 🫘" has `hopsAway: -1` which was filtered out
- The script only connected nodes with valid hop distances

## Solution

Added **co-location detection** to `meshnetmap/inference.py`:

### 1. GPS-Based Detection (`find_colocated_nodes()`)

```python
def find_colocated_nodes(topology_data):
    """Find nodes at the same physical location (same GPS coordinates)"""
    # Groups nodes by GPS coordinates (rounded to 4 decimal places ~11m precision)
    # Returns: [(location, [nodes_at_location]), ...]
```

The function:
- Extracts GPS coordinates from all nodes
- Rounds to 4 decimal places (~11m precision)
- Groups nodes by location
- Returns locations with 2+ nodes

### 2. Automatic Connection Creation

For each co-located group:
- Creates connections between all nodes at that location
- Uses `type: 'colocated'`, `confidence: 'high'`
- Evidence: `'same_gps_location'`
- Assumes excellent SNR (10.0 dB if not available)

### 3. Visualization Updates

The dynamic visualization now:
- Renders co-located connections as **solid green lines**
- Uses **very short link distance** (20px) to keep them close together
- Shows friendly name in modal: "Co-located (same physical location)"
- Prevents physics from separating co-located nodes too much

## Results

With your test data:
```
Found 7 locations with multiple nodes:
  (30.4873, -97.8584): Cool 🫘, Cedar Park 🦙, Matt Mobile
  (30.5398, -97.8059): AirForce 1 Tower, Alpaca Mobile
  (30.4906, -97.7437): MRB Base, MRB Solar
  (30.2154, -97.7895): TonyTanks BBS, TonyTanks ☀️
  (30.4873, -97.7535): CQ X Solar Tower, Meshtastic c8e4
  (30.2776, -97.7535): K Cyber 1, OWL1, zaxTracker1000e, OWL2 - Solar
  (30.2252, -97.8584): Convict Hill, 🔋MustacheRide_Batt

Creating connections for co-located nodes:
  Cool 🫘 ↔ Cedar Park 🦙 (co-located at (30.4873, -97.8584))
  Cool 🫘 ↔ Matt Mobile (co-located at (30.4873, -97.8584))
  Cedar Park 🦙 ↔ Matt Mobile (co-located at (30.4873, -97.8584))
  ... (14 total co-located connections)
```

**Connection stats:**
- Before: 82 connections (missing co-located)
- After: **96 connections** (includes 14 co-located)
- Connection types: `colocated: 14, inferred_direct: 9, inferred_hop: 73`

## Implementation Details

### Files Modified

1. **`meshnetmap/inference.py`** - `find_colocated_nodes()`, connection creation logic
2. **`meshnetmap/visualizer/templates/dynamic_network.html`**
   - Link opacity and dash handling for 'colocated' type
   - Dynamic link distance (20px for colocated, configurable for others)
   - Friendly type names in edge modal
   - Updated legend
3. **`docs/DYNAMIC_VIZ.md`** - Documentation updates

### Connection Data Structure

```json
{
  "from": "!75e98af0",
  "to": "!b794e885",
  "snr": 7.5,
  "type": "colocated",
  "confidence": "high",
  "hops_away": 0,
  "evidence": "same_gps_location",
  "evidence_count": 1,
  "timestamp": "2025-10-07T13:50:00"
}
```

## Benefits

1. **Accurate topology**: Shows actual physical connections
2. **Better visualization**: Co-located nodes appear close together
3. **Source node visibility**: Collection source node is no longer isolated
4. **Multi-device sites**: Handles locations with 3+ devices (e.g., K Cyber 1 with 4 nodes)

## Edge Cases Handled

- Nodes with `hopsAway: -1` (collection source)
- Nodes with `hopsAway: 0` (collection node)
- Missing SNR data (defaults to 10.0 dB)
- Multiple nodes at same site (creates mesh between all)
- GPS precision (rounds to avoid false positives from GPS drift)

## Testing

```bash
# Run inference with co-location detection
meshnetmap infer -i data/network_topology_20251006_221020.json

# Generate dynamic visualization
meshnetmap visualize -i data/network_topology_20251006_221020_topo_v2.json --show --dynamic
```

The visualization now shows "Cool 🫘" and "Cedar Park 🦙" connected with a short green line, accurately representing their physical co-location!
