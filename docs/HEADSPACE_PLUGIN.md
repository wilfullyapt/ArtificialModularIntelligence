# Authoring AMI headspaces

## Quick start

1. Copy `templates/headspace/` (or clone public `ami-headspace-template`).
2. Change `plugin.toml` `id` + `version`.
3. Implement `@ami_tool` methods on your Headspace class.
4. Validate:

```bash
python -m ami.cli plugin validate ./path/to/plugin
python -m ami.cli plugin install ./path/to/plugin --enable
# git-hosted:
python -m ami.cli plugin install user/repo@v0.1.0 --enable
```

## plugin.toml

```toml
id = "my_plugin"
version = "0.1.0"
ami_api_min = "0.1"
exports = ["headspace"]  # optional: gui, blueprint
```

## Exports

`__init__.py` must define/import symbols matching exports:

- `headspace` → `Headspace`
- `gui` → `GUI`
- `blueprint` → `Blueprint`

Recommended: `EXAMPLES` list + `__version__`.

## Tests

Keep domain logic free of PyQt. Unit-test pure helpers; Headspace construction needs full appliance config.

## Mesh peers

If your plugin talks mesh, obey `docs/NEIGHBORS_CONTRACT.md` — do not invent a second peer schema.
