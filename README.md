# IbMarkdownUtil
## Features
### Table of Contents
#### Lifting
Lift the table of contents from the specified Markdown file to all parent Markdown files.

For example:  
Before lifting:
- A/B/C/README.md:
    ```md
    # C
    - [Renamed page 1](Renamed%20page%201.md)
    - [Newly added page 2](Page%201.md)
    ```
- A/B/README.md:
    ```md
    # B
    - ...
    - [C](C/README.md)
      - [Page 1](C/Page%201.md)
    - ...
    ```
- A/README.md:
    ```md
    # A
    - ...
    - [B](B/README.md)
      - ...
      - [C](B/C/README.md)
        - [Page 1](B/C/Page%201.md)
      - ...
    - ...
    ```
After lifting the ToC of A/B/C/README.md by executing `mdutil toc lift A/B/C/README.md`:  
- A/B/README.md:
    ```md
    # B
    - ...
    - [C](C/README.md)
        - [Renamed page 1](C/Renamed%20page%201.md)
        - [Newly added page 2](C/Page%201.md)
    - ...
    ```
- A/README.md:
    ```md
    # A
    - ...
    - [B](B/README.md)
      - ...
      - [C](B/C/README.md)
        - [Renamed page 1](B/C/Renamed%20page%201.md)
        - [Newly added page 2](B/C/Page%201.md)
      - ...
    - ...
    ```