import re
from pathlib import Path
import click

def prefix_each_line(s, prefix):
    return '\n'.join(prefix + line for line in s.splitlines())

def encode_path(path):
    # Reserved characters: !#$&'()*+,/:;=?@[] %
    # Available in Windows filenames: !#$&'()+,;=@[] %
    # Needed escaping in VS Code: # %
    return (str(path)
        .replace('%', '%25')  # must be first
        .replace(' ', '%20').replace('#', '%23')
        .replace('\\', '/')  # not necessary, but we replace it for consistency
    )

def prefix_link_paths(content, prefix):
    return re.sub(r'\]\(([^\)]+)\)', rf']({encode_path(prefix)}\1)', content)

def md_parents(path):
    for dir in path.parents:
        if (dir / 'README.md').exists():
            yield dir / 'README.md'
            if (dir / '.git').exists():
                return
        else:
            return

def find_toc(content):
    return re.search(r'^[-*] +\[[^\]]+\]\([^\)]+\.md\)[\S\s]*?(?=\n\n|^# |\Z)', content, re.MULTILINE)

def find_toc_segment(content, path):
    pattern = rf'^(\s*)[-*] +\[[^\]]+\]\({re.escape(encode_path(path))}\).*(\n\1 +.*)*'
    return re.search(pattern, content, re.MULTILINE)

@click.group()
def cli():
    pass

@cli.group(help='Table of Contents')
def toc():
    pass

@toc.command(help='Lift the table of contents from the Markdown file to all parent Markdown files. See README for a complete example.')
@click.argument('path', type=click.Path(exists=True))
def lift(path):
    path = Path(path)

    it = md_parents(path)
    parent = next(it)
    with open(parent, 'r', encoding='utf8') as f:
        content = f.read()

        try:
            title = content.splitlines()[0].removeprefix('# ')
        except IndexError:
            raise RuntimeError(f'"{parent}" is empty, check if you have saved it')

        toc = find_toc(content)
        if toc is None:
            raise RuntimeError(f'Cannot find ToC in "{parent}"')
        toc = toc[0]

        toc = f'- [{title}]({encode_path(parent.name)})\n' + prefix_each_line(toc, '  ')  #TODO: custom list characters and indentation

    toc_indent = ''
    for ancestor in it:
        with open(ancestor, 'r+', encoding='utf8') as f:
            content = f.read()
            
            newline = ''
            toc_segment = find_toc_segment(content, parent.relative_to(ancestor.parent))
            if toc_segment is not None:
                toc_indent = toc_segment[1]
                toc_segment = slice(toc_segment.start(), toc_segment.end())
            else:
                #TODO: appending is not the best way

                print(f'Cannot find existing ToC segment in "{ancestor}", trying to append after the ToC')

                toc_segment = find_toc(content)
                if toc_segment is not None:
                    toc_segment = slice(toc_segment.end(), toc_segment.end())
                else:
                    print(f'Cannot find ToC in "{ancestor}", trying to append after the title')

                    try:
                        title_len = len(content.splitlines()[0])
                    except IndexError:
                        title_len = 0
                    toc_segment = slice(title_len, title_len)
                toc_indent = toc_indent + '  '
                newline = '\n'
            
            new_toc_segment = newline + prefix_each_line(prefix_link_paths(toc, parent.parent.relative_to(ancestor.parent).as_posix() + '/'), toc_indent)

            new_content = content[:toc_segment.start] + new_toc_segment + content[toc_segment.stop:]

            f.seek(0)
            f.truncate()
            f.write(new_content)

@cli.group(help='Convert')
def conv():
    pass

@conv.group(help='From OneNote-Obsidian note in the clipboard...')
def oneob():
    pass

@oneob.command(help='To Obsidian note (images are not supported)')
def ob():
    import pyperclip

    content = pyperclip.paste()

    # Fix newlines
    content = re.sub('\n\n', '\n', content)
    content = re.sub(r'^#', '\n#', content, flags=re.MULTILINE)

    # Fix lists
    content = re.sub(r'^-   ', r'- ', content, flags=re.MULTILINE)
    content = re.sub(r'^(\d)\.  ', r'\1. ', content, flags=re.MULTILINE)

    # Titles
    if re.search(r'^## ', content, flags=re.MULTILINE) is None:
        content = re.sub(r'^#', '', content, flags=re.MULTILINE)

    # Time markers
    content = re.sub(r'^t(?:\d{6}|\d{4}|\d{2}|~)(?: \S+)?$', r'\n<!--\g<0>-->', content, flags=re.MULTILINE)

    pyperclip.copy(content)

if __name__ == '__main__':
    cli()