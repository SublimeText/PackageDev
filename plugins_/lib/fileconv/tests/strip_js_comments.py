import re

reexpr = r"""
    (                               # Capture code
        (?:
            "(?:\\.|[^"\\])*"           # String literal
            |
            '(?:\\.|[^'\\])*'           # String literal
            |
            (?:[^/\n"']|/[^/*\n"'])+    # Any code besides newlines or string literals
            |
            \n                          # Newline
        )+                          # Repeat
    )|
    (/\*  (?:[^*]|\*[^/])*   \*/)   # Multi-line comment
    |
    (?://(.*)$)                     # Comment
"""
rx = re.compile(reexpr, re.VERBOSE + re.MULTILINE)

# This regex matches with three different subgroups.
# One for code and two for comment contents.
# Below is a example of how to extract those.

code = r"""// this is a comment
var x = 2 * 4 // and this is a comment too
var url = "http://www.google.com/" // and "this" too
url += 'but // this is not a comment' // however this one is
url += 'this "is not a comment' + " and ' neither is this //" // only this

bar = 'http://no.comments.com/' // these // are // comments
bar = 'text // string \' no // more //\\' // comments
bar = 'http://no.comments.com/' /*
multiline */
bar = /var/ // comment

/* comment 1 */
bar = open() /* comment 2 */
bar = open() /* comment 2b */// another comment
bar = open( /* comment 3 */ file) // another comment
"""

parts = rx.findall(code)
print('*' * 80, '\nCode:\n\n',
      ''.join(x[0].strip(' ') for x in parts))
print('*' * 80, '\nMulti line comments:\n\n',
      '\n'.join(x[1] for x in parts if x[1].strip()))
print('*' * 80, '\nOne line comments:\n\n',
      '\n'.join(x[2] for x in parts if x[2].strip()))
