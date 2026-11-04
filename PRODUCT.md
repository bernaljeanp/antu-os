# Product

<!-- impeccable:product-schema 1 -->

## Platform

linux-desktop

Native Linux desktop operating system, not a website. Surfaces are KDE Plasma 6 (Qt/QML themes, Plasma
look-and-feel, KWin decoration), SDDM (QML), Plymouth (boot splash), the systemd console, and first-party Qt/QML apps (Inicio, Biblioteca, Observatorio, Zenit, updates and live diagnostics). This value is outside the schema's web/ios/android/adaptive set on purpose.

## Users

Primary user for the first public release: a gamer with an NVIDIA gaming laptop who comes from Windows and wants
to play on Linux without fighting the system. Daily work, AI-assisted programming and family use (a child playing
Roblox) are real but secondary jobs. Reference machine: Alienware 16X Aurora (Core Ultra 9 275HX, RTX 5070 Laptop,
2560×1600 at 240 Hz).

## Product Purpose

Antu OS is a Chilean gaming Linux distribution: an atomic Arch Linux system for gaming laptops with NVIDIA GPUs.
Its target is a Windows gamer using an NVIDIA laptop who wants a coherent Linux experience. Success: a Windows gamer installs it, plays, and never has to open a terminal to fix it.

## Positioning

The SteamOS-style experience for NVIDIA laptops: Arch freshness and drivers with atomic, image-based updates and
rollback (bootc), plus first-party control of gaming-laptop hardware through Zenit (thermals, lighting, Fn keys,
charge limit) that other distributions lack.

## Operating Context

- Installed from a USB created with USBoot (the user's own tool) or, during the prototype, with
  `scripts/install-to-disk.sh` onto an external disk.
- Updates arrive as whole images; the boot menu offers the previous version.
- The live USB opens a graphical welcome with Try and Install. Installed first boot creates the account through Inicio (systemd-homed), before SDDM.
- Users play through Steam/Proton; anti-cheat games and Roblox have known limits on Linux.

## Capabilities and Constraints

- Base: Arch Linux, bootc (composefs), nvidia-open, KDE Plasma 6.8, SDDM, PipeWire, NetworkManager.
- Prototype with Steam, graphical installer, image signing and a Secure Boot chain in source/CI. VM evidence exists; physical validation is partial and a new image must include each source change.
- Theming must work through KDE/Qt mechanisms and survive atomic updates (shipped in `/usr`, defaults in `/etc/xdg`).
- Performance matters: the system competes with Windows on gaming laptops; visual effects must not cost frames.
- License: code GPL-3.0-or-later, art (wallpapers, logos, icons) CC-BY-SA-4.0. Undecided: final release date.

## Brand Commitments

- Name: **Antu OS** ("Antu" = sun in Mapudungun, also a VLT telescope at Paranal). Tagline in use:
  "Desde los cielos más claros de la Tierra."
- Chilean origin is part of the identity: release codenames are Chilean volcanoes (1.0 "Láscar"), the game mode
  is called "Eclipse", the performance profile "Erupción".
- The StarNovum OS identity (open star, cobalt, pearl surfaces, Sora/Public Sans) is **not binding**: the user chose
  a full redesign; StarNovum is reference only.
- **User-pinned interface (2026-11-01): "un macOS gamer".** macOS structure and finish (top bar, floating dock,
  Spotlight-style launcher, Mission Control-style overview) with the macOS aesthetic: translucent glass, blur and
  soft shadows, dark by default, gamer accents. Window buttons stay on the **right** (Windows habit). This replaces
  the earlier Metro de Santiago direction. It must not copy Apple trademarks, logos or proprietary fonts.

## Evidence on Hand

- Repository: github.com/bernaljeanp/antu-os; image ghcr.io/bernaljeanp/antu-nvidia.
- Reference material only: StarNovum assets in `C:\Users\berna\Desktop\SaaS\StarNovum OS\assets\brand\v1`.
- Related products by the same author: Zenit Engine (github.com/bernaljeanp/zenit-engine), USBoot
  (github.com/bernaljeanp/usboot).
- No users, testimonials, benchmarks or press exist yet; do not invent them.

## Product Principles

1. NVIDIA laptops first: every decision is judged on the reference gaming laptop.
2. Never make the user fix the system: atomic updates, rollback, and clear explanations over terminal work.
3. Spanish first, neutral Latin American Spanish with a clear, close tone; English as second language.
4. Frames over flourish: measure effects on real hardware before accepting a performance claim.
5. Honest about limits: say what does not work (anti-cheat, Roblox) instead of hiding it.

## Accessibility & Inclusion

- Readable at 2560×1600 with fractional scaling; text contrast at least WCAG AA.
- Full keyboard operation of system surfaces (login, first boot, game mode) for controller- and keyboard-driven use.

## Visual decision, 2026-11-03

User-approved: matte graphite, glass confined to headers/brand surfaces, lava accents; original obsidian/silver 3D icons. AntuObsidiana and AntuSalar palettes. See DESIGN.md and docs/REFINAMIENTO-VISUAL-2026-11-03.md for implementation, measured contrast and remaining physical checks.
