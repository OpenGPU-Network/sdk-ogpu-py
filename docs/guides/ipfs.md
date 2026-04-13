# IPFS

Off-chain content (source metadata, task configs, response payloads)
lives on IPFS. On-chain transactions only carry URLs, keeping gas costs
bounded regardless of payload size.

Most of the time the SDK handles this transparently:

- `client.publish_source(info)` uploads the source metadata for you
- `client.publish_task(info)` uploads the task config
- `Source.get_metadata()` / `Task.get_metadata()` fetch those back
- `Response.fetch_data()` fetches confirmed response payloads

But if you need to produce response content yourself (as a provider)
or publish arbitrary metadata, `ogpu.ipfs` is the public surface.

## Publishing

```python
from ogpu import publish_to_ipfs

# Dict → JSON → IPFS
url = publish_to_ipfs(
    {"result": "cat", "confidence": 0.97},
    filename="response.json",
)
print(url)   # "https://cipfs.ogpuscan.io/ipfs/Qm..."
```

`publish_to_ipfs` POSTs to the OGPU pinning service at
`capi.ogpuscan.io`. Accepts a dict (JSON-serialized) or a raw string.
Returns a gateway URL.

## Fetching

```python
from ogpu import fetch_ipfs_json

payload = fetch_ipfs_json("https://cipfs.ogpuscan.io/ipfs/Qm...")
print(payload["result"])
```

`fetch_ipfs_json` does a standard HTTP GET against any gateway URL and
parses the body as JSON. Works with OGPU's pinning service URLs, public
gateways, or your own node.

## Typical provider flow

A provider running a real compute source produces output, uploads it
to IPFS, then submits the URL as the on-chain `data` field of a
response. The submission step happens **inside the docker source
runtime**, not from this SDK — `submit_response` is intentionally not
exposed in `ogpu.client`, `ogpu.protocol`, or `ogpu.agent`, because a
freely callable `submit_response` would let any provider key fabricate
responses without doing real work.

The IPFS upload is the part the SDK does help with. From inside your
source handler:

```python
from ogpu import publish_to_ipfs

def predict(input_data):
    # 1. Run the actual compute
    output = run_model(input_data)

    # 2. Upload the output to IPFS
    payload_url = publish_to_ipfs(output, filename="response.json")

    # 3. Return the URL — the source runtime turns it into an
    #    on-chain submitResponse() call signed by the provider.
    return {"url": payload_url, "result": output}
```

## Typical client flow

After confirming a response, fetch the content:

```python
from ogpu.protocol import Task

task = Task.load("0xTASK")
final = task.get_confirmed_response()

if final:
    url = final.get_data()         # IPFS URL
    payload = final.fetch_data()    # dict — one HTTP GET
    print(payload["result"])
```

`Response.fetch_data()` is a thin convenience that calls
`fetch_ipfs_json(response.get_data())`. Two methods because they have
different cost contracts:

- `get_data()` is **local** — just reads the URL field
- `fetch_data()` is **network I/O** — follows the URL

## Errors

Both functions raise typed errors:

```python
from ogpu.types import IPFSFetchError, IPFSGatewayError

try:
    payload = fetch_ipfs_json("https://...")
except IPFSGatewayError as e:
    print(f"gateway returned {e.status_code}")
except IPFSFetchError as e:
    print(f"network or JSON error: {e.reason}")
```

See [errors](errors.md) for the full `IPFSError` hierarchy.

## What's not supported

- **Binary content.** `fetch_ipfs_json` only parses JSON. If the source
  produces binary output (model weights, images, video), use the raw
  URL from `get_data()` and fetch it with your own HTTP client.
- **Custom gateway.** The publish endpoint is OGPU-specific
  (`capi.ogpuscan.io`). Fetching works against any gateway, but
  publishing always goes to OGPU's pinning service.
- **Pinning control.** You can't pin or unpin specific CIDs from the
  SDK. Content uploaded via `publish_to_ipfs` is automatically pinned
  by the OGPU service.

## Next

- [Responses](responses.md) — the workflow that uses `fetch_data()`
- [Reading state](reading-state.md) — `get_metadata()` on `Source` and `Task`
- [API reference: ogpu.ipfs](../reference/ipfs.md)
