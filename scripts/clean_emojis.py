import os
import re

EMOJI_PATTERN = re.compile(
    r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2b50-\u2b55]|[\u2300-\u23ff]|[\ufe00-\ufe0f]|[⬡▸◆●▪✦§✓★☆⚡✨🔥💡🔧🛡🔑🚀🌐📦🎯📝🔍🔎📁💻🖥🌍🛠📖]'
)

def clean_file_content(content: str, filepath: str) -> str:
    lines = content.splitlines()
    new_lines = []

    for line in lines:
        cleaned = line

        # 1. Clean Markdown Headings: e.g. '# Protutech Documentation 🚀'
        # or '## ⬡ Ecosystem Architecture' or '## [#] Anti Reverse Engineering Boundary'
        if cleaned.lstrip().startswith('#'):
            # Strip trailing emojis from headings
            cleaned = re.sub(r'\s*[\U00010000-\U0010ffff\u2600-\u27bf\ufe00-\ufe0f\u2b50-\u2b55⬡▸◆●▪✦§✓★☆⚡✨🔥💡🔧🛡🔑🚀🌐📦🎯📝🔍🔎📁💻🖥🌍🛠📖]+\s*$', '', cleaned)
            # Strip leading symbol/bracket prefixes after '#' marks
            # e.g. '## ⬡ Foo' -> '## Foo', '## [#] Foo' -> '## Foo', '## § Foo' -> '## Foo'
            cleaned = re.sub(
                r'^(#+\s*)(?:\[#\]|\[i\]|\[!\]|[⬡▸◆●▪✦§✓★☆⚡✨🔥💡🔧🛡🔑🚀🌐📦🎯📝🔍🔎📁💻🖥🌍🛠📖])\s*',
                r'\1',
                cleaned
            )
            # In case multiple symbols exist, repeat once
            cleaned = re.sub(
                r'^(#+\s*)(?:\[#\]|\[i\]|\[!\]|[⬡▸◆●▪✦§✓★☆⚡✨🔥💡🔧🛡🔑🚀🌐📦🎯📝🔍🔎📁💻🖥🌍🛠📖])\s*',
                r'\1',
                cleaned
            )

        # 2. Clean Mermaid Diagram labels: e.g. User["▸ User / Agent"] or SFU["☁️ Homelab SFU"]
        # or subgraph ValveWorld["▸ CS2 World Space"] or subgraph CalibrationConfig["§ Calibration"]
        # or subgraph PixelTransform["[#] 1024x1024 Radar Matrix"]
        cleaned = re.sub(
            r'(\[\"(?:subgraph\s+)?)\[#\]\s*',
            r'\1',
            cleaned
        )
        cleaned = re.sub(
            r'(\[\"(?:subgraph\s+)?)\[i\]\s*',
            r'\1',
            cleaned
        )
        cleaned = re.sub(
            r'(\[\"(?:subgraph\s+)?)[⬡▸◆●▪✦§✓★☆⚡✨🔥💡🔧🛡🔑🚀🌐📦🎯📝🔍🔎📁💻🖥🌍🛠📖\U00010000-\U0010ffff\u2600-\u27bf\ufe00-\ufe0f]\s*',
            r'\1',
            cleaned
        )

        # 3. Clean Directory Tree ASCII formatting: e.g. '├── 📁 server/' -> '├── server/'
        cleaned = re.sub(r'([├└│─\s]+)📁\s*', r'\1', cleaned)

        # 4. Clean Quick Navigation cards and list bullets:
        # e.g. '-   ▸ **Protutech Suite**' -> '-   **Protutech Suite**'
        cleaned = re.sub(r'^((\s*[-*]\s*))[⬡▸◆●▪✦§✓]\s*', r'\1', cleaned)

        # 5. Clean Link texts:
        # e.g. '[▸ View Architecture]' -> '[View Architecture]'
        # e.g. '[Read Envelope Encryption Deep Dive ▸]' -> '[Read Envelope Encryption Deep Dive]'
        cleaned = re.sub(r'\[[⬡▸◆●▪✦§✓]\s*', '[', cleaned)
        cleaned = re.sub(r'\s*[⬡▸◆●▪✦§✓]\]', ']', cleaned)

        # 6. Specific phrases and messages
        cleaned = cleaned.replace('✓ Drive', 'Drive')
        cleaned = cleaned.replace('✓ Target', 'Target')

        # Clean callout title spaces, e.g. ???+ note " Complete -> ???+ note "Complete
        cleaned = re.sub(r'(\?\?\?\+?\s+\w+\s+\")\s+', r'\1', cleaned)

        # 7. Remove any remaining stray emojis or decorative symbols
        # Check if any remain in line
        if EMOJI_PATTERN.search(cleaned):
            # Remove any standalone symbol in the line
            cleaned = EMOJI_PATTERN.sub('', cleaned)
            # Clean up potential double spaces caused by symbol deletion
            cleaned = re.sub(r' +', ' ', cleaned)

        new_lines.append(cleaned)

    result = '\n'.join(new_lines) + '\n'
    return result

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_exts = ('.md', '.yml')
    modified_count = 0
    total_files = 0

    for dirpath, _, filenames in os.walk(root_dir):
        if '.git' in dirpath or 'site' in dirpath or '.system_generated' in dirpath:
            continue
        for fname in filenames:
            if fname.endswith(target_exts):
                total_files += 1
                fpath = os.path.join(dirpath, fname)
                with open(fpath, 'r', encoding='utf-8') as fh:
                    orig_content = fh.read()

                cleaned = clean_file_content(orig_content, fpath)

                if cleaned != orig_content:
                    with open(fpath, 'w', encoding='utf-8') as fh:
                        fh.write(cleaned)
                    print(f"Cleaned: {os.path.relpath(fpath, root_dir)}")
                    modified_count += 1

    print(f"\nProcessing complete: {modified_count} of {total_files} files updated.")

    # Verification pass
    print("\nRunning verification pass for any remaining emojis or symbols...")
    remaining_count = 0
    for dirpath, _, filenames in os.walk(root_dir):
        if '.git' in dirpath or 'site' in dirpath or '.system_generated' in dirpath or 'scripts' in dirpath:
            continue
        for fname in filenames:
            if fname.endswith(target_exts):
                fpath = os.path.join(dirpath, fname)
                with open(fpath, 'r', encoding='utf-8') as fh:
                    c = fh.read()
                matches = EMOJI_PATTERN.findall(c)
                if matches:
                    print(f"REMAINING in {os.path.relpath(fpath, root_dir)}: {[ascii(m) for m in set(matches)]}")
                    remaining_count += len(matches)

    print(f"Total remaining symbols/emojis: {remaining_count}")

if __name__ == '__main__':
    main()
