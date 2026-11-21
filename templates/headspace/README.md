# AMI headspace template

Public starter for third-party **Headspace** plugins.

## Contract

See AMI monorepo `docs/NEIGHBORS_CONTRACT.md` (mesh/directory) and:

- `plugin.toml` — `id`, `version`, `ami_api_min`, `exports`
- `__init__.py` must export `Headspace` (optional `GUI`, `Blueprint`)
- Tools use `@ami_tool` on the Headspace class

## Validate + install

```bash
# from AMI checkout
python -m ami.cli plugin validate ./templates/headspace
python -m ami.cli plugin install /path/to/your-plugin@v0.1.0 --enable
# or from GitHub after you publish:
# python -m ami.cli plugin install you/your-headspace@v0.1.0 --enable
```

## Layout

```
plugin.toml
__init__.py      # Headspace + EXAMPLES + __version__
headspace.py     # @ami_tool methods
skills/          # optional seeded markdown skills
```

Keep GUI/Blueprint out until you need glass or Flask routes.
