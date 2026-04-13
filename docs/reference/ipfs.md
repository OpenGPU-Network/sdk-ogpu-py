# `ogpu.ipfs`

Publish and fetch off-chain content. IPFS is how the OGPU protocol
keeps transactions cheap — only URLs go on-chain, the actual content
(source metadata, task configs, response payloads, model weights,
images) lives off-chain on IPFS.

Most SDK workflows use these functions internally:

- `client.publish_source(info)` uploads source metadata for you.
- `client.publish_task(info)` uploads the task config.
- `Source.get_metadata()` / `Task.get_metadata()` fetch them back.
- `Response.fetch_data()` fetches confirmed response payloads.

You only need to call `publish_to_ipfs` or `fetch_ipfs_json` directly
when you're producing real response payloads as a provider or want
direct fetch control. Both functions are re-exported at the top level:

```python
from ogpu import publish_to_ipfs, fetch_ipfs_json
```

The publish endpoint is OGPU-specific (`capi.ogpuscan.io/file/create`)
and cannot be overridden. Fetching works against any IPFS gateway URL.
See the [IPFS guide](../guides/ipfs.md) for the workflow.

---



::: ogpu.ipfs.publish.publish_to_ipfs
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.ipfs.fetch.fetch_ipfs_json
    options:
      show_root_heading: true
      heading_level: 3
