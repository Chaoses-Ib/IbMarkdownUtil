import re
from pathlib import Path
import fire

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

class ToC:
    def lift(self, path):
        '''
        Lift the table of contents from the specified Markdown file to all parent Markdown files.

        For example:\n
        Before lifting:
        ```
        A/B/C/README.md:
            # C
            - [Renamed page 1](Renamed%20page%201.md)
            - [Newly added page 2](Page%202.md)
        A/B/README.md:
            # B
            - ...
            - [C](C/README.md)
              - [Page 1](C/Page%201.md)
            - ...
        A/README.md:
            # A
            - ...
            - [B](B/README.md)
              - ...
              - [C](B/C/README.md)
                - [Page 1](B/C/Page%201.md)
              - ...
            - ...
        ```
        After lifting A/B/C/README.md:
        ```
        A/B/README.md:
            # B
            - ...
            - [C](C/README.md)
              - [Renamed page 1](C/Renamed%20page%201.md)
              - [Newly added page 2](C/Page%202.md)
            - ...
        A/README.md:
            # A
            - ...
            - [B](B/README.md)
              - ...
              - [C](B/C/README.md)
                - [Renamed page 1](B/C/Renamed%20page%201.md)
                - [Newly added page 2](B/C/Page%202.md)
              - ...
            - ...
        ```
        '''

        path = Path(path)

        it = md_parents(path)
        parent = next(it)
        with open(parent, 'r', encoding='utf8') as f:
            content = f.read()

            title = content.splitlines()[0].removeprefix('# ')

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

                        title_len = len(content.splitlines()[0])
                        toc_segment = slice(title_len, title_len)
                    toc_indent = toc_indent + '  '
                    newline = '\n'
                
                new_toc_segment = newline + prefix_each_line(prefix_link_paths(toc, parent.parent.relative_to(ancestor.parent).as_posix() + '/'), toc_indent)

                new_content = content[:toc_segment.start] + new_toc_segment + content[toc_segment.stop:]

                f.seek(0)
                f.truncate()
                f.write(new_content)

class CLI:
    def __init__(self):
        self.toc = ToC()

if __name__ == '__main__':
    fire.Fire(CLI)