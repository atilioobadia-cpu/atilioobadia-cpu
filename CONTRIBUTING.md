# Contributing

Thanks for taking an interest. This repository is the profile page, so most of the useful work
happens in the project repositories listed in [`docs/PROJECTS.md`](docs/PROJECTS.md).

## Where to start

- **Bug or broken behaviour:** open an issue on the repository where it happens, with steps to
  reproduce and what you expected instead.
- **Feature or improvement:** open an issue describing the problem before writing the code. It
  saves you building something that does not fit the design.
- **Documentation:** corrections and clarifications are always welcome, including one-line fixes.

## Pull requests

1. Check for an existing issue or open one first.
2. Branch from `main` as `feat/<scope>`, `fix/<scope>` or `docs/<scope>`.
3. Keep the change focused: one logical change per pull request.
4. Match the surrounding style, and run the project's lint, typecheck and tests before pushing.
5. Update the documentation in the same pull request when behaviour, fields or rules change.

Commit messages follow the conventional format: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.

## What not to send

- Real member, customer or staff data, in any form, including screenshots.
- Credentials, tokens or `.env` files.
- Large binaries or generated build output.

## Questions

Open an issue, or email [atilioobadia@gmail.com](mailto:atilioobadia@gmail.com).

## Profile artwork

The panels on the profile page are generated, not hand-drawn. Edit
[`tools/build-profile-svgs.py`](tools/build-profile-svgs.py) and run:

```powershell
python tools/build-profile-svgs.py
```

It writes the light SVGs to `assets/` and the dark variants to `assets/dark/`, measuring
text with the real font metrics so nothing overflows.
