# Glacier TEX Editor

Glacier TEX Editor can open and edit the `.TEX` texture archives used by Kane & Lynch 2:
Dog Days uses the same Glacier TEX family as the other supported Glacier games. The editor
is useful for inspecting entries and making hand-authored texture changes, including
character and HUD textures.

The screenshot supplied during the engine research shows a Dog Days archive with DXT1,
DXT3, RGBA, PALN, I8, and U8V8 entries. The archive contains 1,266 texture entries in
that example.

## Roles in this project

- Use Glacier TEX Editor for visual inspection and deliberate one-off edits.
- Use `tools/kl_texmat.py` for scripted merges, ID remapping, deduplication, and
  round-trip validation.
- Keep texture edits inside a build folder until the complete level checks pass.
- Do not commit original or modified game archives to this repository.

The editor should not be assumed to preserve project-specific relationships automatically.
After a manual edit, rerun the relevant map checks and verify that texture IDs, mipmaps,
animated or cube-map references, material references, and the 4096-entry Dog Days limit
remain valid.
