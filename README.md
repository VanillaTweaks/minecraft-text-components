# minecraft-text-components

A Python library for manipulating Minecraft's raw JSON text components

## minify `beet` plugin

This library comes bundled with an optional beet plugin to automatically minify all text components inside commands. To use, install the optional dependency as described below:

```bash
pip install minecraft-text-components[beet]
```

Then, you can require the plugin inside your beet configuration file:

```yaml
require:
    - minecraft_text_components.contrib.beet_minify

pipeline:
    - mecha
```
