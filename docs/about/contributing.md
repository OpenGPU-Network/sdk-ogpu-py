# Contributing

The SDK is open source under the MIT license. Contributions welcome.

## Development setup

```bash
git clone https://github.com/OpenGPU-Network/sdk-ogpu-py.git
cd sdk-ogpu-py
pip install -e ".[dev]"
```

This pulls in `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy`, `ruff`,
and `nbformat`.

## Running the test suite

```bash
pytest tests/                    # full suite (all mocked, no chain)
pytest tests/unit/test_vault.py  # one module
pytest tests/ -k "vault"         # by keyword
```

Every test in `tests/unit/` is mock-based — nothing hits a real chain.
The suite runs in under 2 seconds.

## Type checking and lint

```bash
mypy ogpu/       # strict mode, configured in pyproject.toml
ruff check ogpu/ # lint
ruff format ogpu/  # format
```

Run all three before opening a PR.

## Layer discipline

The SDK is organized by layer:

```
types  chain  ipfs          ← leaves, no outward dependencies
   ↑
protocol                     ← 1:1 contract wrappers
   ↑
client / agent / events      ← role-first workflows
```

New code must respect this direction:

- Nothing under `ogpu/types/` may import from higher layers
- `ogpu/protocol/` may import from `types`, `chain`, `ipfs` but not `client`
- `ogpu/client/`, `ogpu/agent/`, `ogpu/events/` sit at the top

If you find yourself wanting to import a higher layer from a lower one,
the code probably belongs in the higher layer.

## Adding a new method on an instance class

Example: adding `Task.get_something_new()`.

1. Check the `TaskAbi.json` to find the underlying function name
2. Add the method to `ogpu/protocol/task.py`:
   ```python
   def get_something_new(self) -> int:
       return int(self._contract().functions.somethingNew().call())
   ```
3. Add a unit test in `tests/unit/test_instance_task.py`:
   ```python
   def test_get_something_new(self):
       c = _mc(somethingNew=42)
       t, p = self._t(c)
       with p:
           assert t.get_something_new() == 42
   ```
4. If it's a write method, update `REVERT_PATTERN_MAP` in `_base.py`
   with any new revert strings.
5. Run `pytest`, `mypy`, `ruff`.

## Documentation

Docs live in `docs/` and build with mkdocs-material:

```bash
pip install -r docs-requirements.txt
mkdocs serve   # local preview at http://localhost:8000
mkdocs build --strict   # CI-equivalent build
```

API reference pages use `mkdocstrings` to pull docstrings from source.
Adding a new method with a Google-style docstring is enough — it will
appear in the reference automatically.

## Commit conventions

The repo uses conventional commits (`feat:`, `fix:`, `docs:`, `chore:`,
`refactor:`, `test:`).

## Reporting issues

File issues at
[github.com/OpenGPU-Network/sdk-ogpu-py/issues](https://github.com/OpenGPU-Network/sdk-ogpu-py/issues).

Please include:

- Python version
- SDK version (`python -c "import ogpu; print(ogpu.__file__)"`)
- Minimal reproduction code
- Expected vs actual behavior
- Full traceback if it's a crash

## License

MIT. See [LICENSE](https://github.com/OpenGPU-Network/sdk-ogpu-py/blob/main/LICENSE).
