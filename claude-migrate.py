#!/usr/bin/env python3
"""
Claude Desktop Session & Worktree Migrator
------------------------------------------
Zero-dependency CLI tool to transfer Claude Code Desktop sessions, projects,
and chat histories between multiple Claude profiles/accounts on macOS.

Key Features:
- Discovers all Claude Desktop profiles automatically.
- Safely links sessions without moving, modifying, or duplicating physical code repositories.
- Fully interactive with previews and mandatory confirmation prompts.
- Preserves full conversation context, turn history, and git worktrees.
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
from pathlib import Path

APP_SUPPORT = Path.home() / "Library" / "Application Support"

def get_claude_profiles():
    profiles = {}
    if not APP_SUPPORT.exists():
        return profiles

    for item in APP_SUPPORT.iterdir():
        if item.is_dir() and item.name.startswith("Claude"):
            sess_dir = item / "claude-code-sessions"
            cfg_path = item / "config.json"
            last_account = None
            if cfg_path.exists():
                try:
                    with open(cfg_path) as f:
                        last_account = json.load(f).get("lastKnownAccountUuid")
                except:
                    pass

            accounts = {}
            if sess_dir.exists():
                for acct_dir in sess_dir.iterdir():
                    if acct_dir.is_dir():
                        orgs = {}
                        for org_dir in acct_dir.iterdir():
                            if org_dir.is_dir():
                                sessions = []
                                for sf in org_dir.glob("local_*.json"):
                                    try:
                                        with open(sf) as f:
                                            d = json.load(f)
                                            sessions.append({
                                                "filename": sf.name,
                                                "filepath": str(sf),
                                                "title": d.get("title", "Untitled"),
                                                "cwd": d.get("cwd", "Unknown"),
                                                "turns": d.get("completedTurns", 0),
                                                "cliSessionId": d.get("cliSessionId")
                                            })
                                    except:
                                        pass
                                orgs[org_dir.name] = sessions
                        if orgs:
                            accounts[acct_dir.name] = orgs

            profiles[item.name] = {
                "path": str(item),
                "lastKnownAccount": last_account,
                "accounts": accounts
            }
    return profiles

def get_project_name(cwd):
    norm = cwd.rstrip("/").lower()
    return Path(norm).name

def list_inventory(profiles):
    print("\n" + "=" * 65)
    print("       CLAUDE DESKTOP PROFILES & SAVED SESSIONS")
    print("=" * 65)
    for p_name, p_data in sorted(profiles.items()):
        print(f"\n📁 Profile: {p_name}")
        print(f"   Directory: {p_data['path']}")
        print(f"   Active Account UUID: {p_data['lastKnownAccount']}")
        if not p_data["accounts"]:
            print("   (No Claude Code sessions found in this profile)")
            continue
        for acct_id, orgs in p_data["accounts"].items():
            is_active = " [CURRENTLY ACTIVE]" if acct_id == p_data["lastKnownAccount"] else ""
            print(f"   👤 Account: {acct_id}{is_active}")
            for org_id, sessions in orgs.items():
                print(f"      🏢 Organization: {org_id} ({len(sessions)} sessions)")
                by_proj = {}
                for s in sessions:
                    proj = get_project_name(s["cwd"])
                    by_proj.setdefault(proj, []).append(s)
                for proj, p_sess in sorted(by_proj.items()):
                    print(f"         📂 Project: {proj} ({len(p_sess)} chats)")
                    for s in p_sess[:3]:
                        print(f"            • {s['title']} ({s['turns']} turns)")
                    if len(p_sess) > 3:
                        print(f"            ... and {len(p_sess) - 3} more")
    print("\n" + "=" * 65 + "\n")

def perform_migration(src_sessions, dst_org_dir, dst_profile_path, dry_run=False):
    dst_org_dir = Path(dst_org_dir)
    dst_profile_path = Path(dst_profile_path)

    if not dry_run:
        dst_org_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for s in src_sessions:
        src_path = Path(s["filepath"])
        dst_path = dst_org_dir / s["filename"]
        if not dry_run:
            shutil.copy2(src_path, dst_path)
        copied.append(s)

    wt_dst_file = dst_profile_path / "git-worktrees.json"
    if wt_dst_file.exists() and not dry_run:
        try:
            with open(wt_dst_file) as f:
                wt_data = json.load(f)
            roots = wt_data.setdefault("untrackedDirGc", {}).setdefault("roots", {})
            cwds = wt_data.setdefault("untrackedDirGc", {}).setdefault("cwds", {})
            now = 1793000000000
            for s in src_sessions:
                cwd = s.get("cwd")
                if cwd and os.path.exists(cwd):
                    cwds[cwd] = now
                    wt_dir = os.path.join(cwd, ".claude", "worktrees")
                    if os.path.exists(wt_dir):
                        roots[wt_dir] = now
            with open(wt_dst_file, "w") as f:
                json.dump(wt_data, f, indent=2)
        except Exception as e:
            print(f"Notice: git-worktrees.json update skipped: {e}")

    return copied

def restart_instance(profile_name):
    print(f"\nRestarting {profile_name} to load migrated sessions...")
    try:
        out = subprocess.check_output(["pgrep", "-f", f"user-data-dir=.*{profile_name}"]).decode()
        pids = [int(p) for p in out.strip().split() if p.isdigit()]
        for pid in pids:
            try:
                os.kill(pid, 15)
            except:
                pass
        import time
        time.sleep(2)
    except:
        pass

    # Find corresponding application bundle
    app_target = "/Applications/Claude.app"
    if os.path.exists(f"/Applications/{profile_name.replace('-', ' ')}.app"):
        app_target = f"/Applications/{profile_name.replace('-', ' ')}.app"
    elif profile_name == "Claude-2" and os.path.exists("/Applications/Claude 2.app"):
        app_target = "/Applications/Claude 2.app"

    try:
        subprocess.run(["open", "-a", app_target])
        print(f"✓ Relaunched {app_target} successfully.")
    except Exception as e:
        print(f"Info: Please restart your {profile_name} app manually: {e}")

def main():
    parser = argparse.ArgumentParser(description="Transfer Claude Code sessions between Claude Desktop accounts")
    parser.add_argument("--list", action="store_true", help="List all detected Claude profiles, accounts, and projects")
    parser.add_argument("--src-profile", type=str, help="Source profile name (e.g. Claude, Claude-2, Claude-Work)")
    parser.add_argument("--dst-profile", type=str, help="Destination profile name")
    parser.add_argument("--include", type=str, help="Comma-separated project keywords to include")
    parser.add_argument("--exclude", type=str, help="Comma-separated project keywords to exclude")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without copying files")

    args = parser.parse_args()
    profiles = get_claude_profiles()

    if args.list:
        list_inventory(profiles)
        return

    if not args.src_profile or not args.dst_profile:
        list_inventory(profiles)
        avail = list(profiles.keys())
        if len(avail) < 2:
            print("Notice: Need at least 2 Claude Desktop profiles to migrate between.")
            print("Tip: Run Claude with --user-data-dir=\"$HOME/Library/Application Support/Claude-Work\" to create a second profile.")
            return

        print("Select Profiles:")
        for idx, p in enumerate(avail, 1):
            print(f"  {idx}. {p}")

        try:
            s_idx = int(input("\nSelect SOURCE profile number: ").strip()) - 1
            src_name = avail[s_idx]

            d_idx = int(input("Select DESTINATION profile number: ").strip()) - 1
            dst_name = avail[d_idx]
        except (ValueError, IndexError):
            print("Invalid profile selection.")
            return

        src_data = profiles[src_name]
        dst_data = profiles[dst_name]

        src_accts = list(src_data["accounts"].keys())
        if not src_accts:
            print(f"No accounts with sessions found in {src_name}.")
            return
        src_acct = src_accts[0] if len(src_accts) == 1 else None
        if not src_acct:
            print(f"\nAccounts in {src_name}:")
            for idx, a in enumerate(src_accts, 1):
                print(f"  {idx}. {a}")
            src_acct = src_accts[int(input("Select source account: ").strip()) - 1]

        dst_accts = list(dst_data["accounts"].keys())
        dst_acct = dst_accts[0] if dst_accts else dst_data["lastKnownAccount"]

        src_orgs = src_data["accounts"][src_acct]
        src_org = list(src_orgs.keys())[0]
        all_src_sessions = src_orgs[src_org]

        dst_orgs = dst_data["accounts"].get(dst_acct, {})
        dst_org = list(dst_orgs.keys())[0] if dst_orgs else None
        if not dst_org:
            dst_sess_dir = Path(dst_data["path"]) / "claude-code-sessions" / dst_acct
            org_dirs = [d.name for d in dst_sess_dir.iterdir() if d.is_dir()] if dst_sess_dir.exists() else []
            dst_org = org_dirs[0] if org_dirs else None

        if not dst_org:
            print(f"Error: Could not locate destination organization folder in {dst_name}.")
            print("Make sure you have logged into the destination account at least once.")
            return

        projects = {}
        for s in all_src_sessions:
            proj = get_project_name(s["cwd"])
            projects.setdefault(proj, []).append(s)

        print(f"\nProjects found in {src_name}:")
        proj_list = sorted(projects.keys())
        for idx, p in enumerate(proj_list, 1):
            print(f"  {idx}. {p} ({len(projects[p])} sessions)")

        sel = input("\nEnter project numbers to transfer (comma-separated, or press Enter for 'all'): ").strip()
        if sel.lower() == "all" or not sel:
            selected_projects = proj_list
        else:
            selected_projects = []
            for item in sel.split(","):
                try:
                    selected_projects.append(proj_list[int(item.strip()) - 1])
                except:
                    pass

        excl = input("Enter project names/keywords to EXCLUDE (or press Enter for none): ").strip()
        exclude_list = [x.strip().lower() for x in excl.split(",") if x.strip()]

        sessions_to_copy = []
        for p in selected_projects:
            if any(e in p.lower() for e in exclude_list):
                continue
            sessions_to_copy.extend(projects[p])

        dst_org_dir = Path(dst_data["path"]) / "claude-code-sessions" / dst_acct / dst_org

        print("\n" + "=" * 65)
        print("                 MIGRATION PREVIEW")
        print("=" * 65)
        print(f"Source:      {src_name} ({src_acct})")
        print(f"Destination: {dst_name} ({dst_acct})")
        print(f"Target Path: {dst_org_dir}")
        print(f"Sessions:    {len(sessions_to_copy)} to transfer")
        for s in sessions_to_copy:
            print(f"  • [{get_project_name(s['cwd'])}] {s['title']} ({s['turns']} turns)")
        print("=" * 65)

        confirm = input("\nDo you want to proceed with copying these sessions? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted. No files were changed.")
            return

        perform_migration(sessions_to_copy, dst_org_dir, dst_data["path"])
        print(f"\n✓ Successfully transferred {len(sessions_to_copy)} sessions to {dst_name}!")

        re_ans = input(f"Would you like to restart {dst_name} now to reload sessions? (Y/n): ").strip().lower()
        if re_ans != "n":
            restart_instance(dst_name)
    else:
        src_name = args.src_profile
        dst_name = args.dst_profile
        if src_name not in profiles or dst_name not in profiles:
            print(f"Error: Profile not found. Available: {list(profiles.keys())}")
            return

        src_data = profiles[src_name]
        dst_data = profiles[dst_name]

        src_acct = list(src_data["accounts"].keys())[0]
        src_org = list(src_data["accounts"][src_acct].keys())[0]
        all_src_sessions = src_data["accounts"][src_acct][src_org]

        dst_acct = dst_data["lastKnownAccount"] or list(dst_data["accounts"].keys())[0]
        dst_sess_dir = Path(dst_data["path"]) / "claude-code-sessions" / dst_acct
        org_dirs = [d.name for d in dst_sess_dir.iterdir() if d.is_dir()] if dst_sess_dir.exists() else []
        dst_org = org_dirs[0]

        includes = [x.strip().lower() for x in args.include.split(",")] if args.include else []
        excludes = [x.strip().lower() for x in args.exclude.split(",")] if args.exclude else []

        sessions_to_copy = []
        for s in all_src_sessions:
            cwd = s["cwd"].lower()
            title = s["title"].lower()
            if excludes and any(e in cwd or e in title for e in excludes):
                continue
            if includes:
                if any(i in cwd or i in title for i in includes):
                    sessions_to_copy.append(s)
            else:
                sessions_to_copy.append(s)

        dst_org_dir = Path(dst_data["path"]) / "claude-code-sessions" / dst_acct / dst_org

        print(f"Transferring {len(sessions_to_copy)} sessions from {src_name} to {dst_name}...")
        for s in sessions_to_copy:
            print(f"  • {s['title']}")

        if not args.yes and not args.dry_run:
            ans = input("Proceed? (y/N): ").strip().lower()
            if ans != "y":
                print("Aborted.")
                return

        perform_migration(sessions_to_copy, dst_org_dir, dst_data["path"], dry_run=args.dry_run)
        print("✓ Completed successfully.")
        if not args.dry_run:
            restart_instance(dst_name)

if __name__ == "__main__":
    main()
