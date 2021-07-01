# Project: Tryceratops

![tryceratops logo](./tryceratops-logo.png)

<a href="https://pypi.org/project/tryceratops/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/tryceratops">
</a>

<a href="https://pepy.tech/project/tryceratops/">
<img alt="Downloads" src="https://static.pepy.tech/personalized-badge/tryceratops?period=total&units=international_system&left_color=grey&right_color=blue&left_text=%F0%9F%A6%96%20Downloads">
</a>

**Source Code:** https://github.com/guilatrova/tryceratops

**Stack:** Python

---

It's a linter to help python developers write nice and clean `try` / `except` blocks.

## Why a linter?

I got very interested in writing a linter, mostly because I had no idea how I would be able to use Python code to lint more Python code.

https://twitter.com/guilatrova/status/1406205142224023552

It seemed so hard that I wondered if I would be able to do it.

Besides this I realized it could add more value because...

### People seemed interested into writing better exceptions in Python

After publishing my article on [Handling exceptions in Python like a pro 🐍 💣](https://blog.guilatrova.dev/handling-exceptions-in-python-like-a-pro/) I got so surprised by the increased traffic in this blog:

https://twitter.com/guilatrova/status/1395347517131329537

It went from ~1-2 people daily (me and my mom probably) to ~20-50 people daily.

![traffic today](traffic-today.png)

So it made me think that writing good and well defined try/except blocks would be something that developers would like.

### It's hard to track it

Without linters, would you be able manage every unused import in your project? Maybe, but it would be a pain and it's very easy to slip by.

That's another reason that made me realize that having a tool to check my code and give me feedback is a great way to keep the quality without the struggle.

## Processing Python Code

The first question is: How can Python understand Python?
I started considering reading a bare string (e.g. `def func(): return 1`) and reading it token by token. Thank God it was not required. Python has support to a lib named `ast` that made it easy.

### Interpreting code with AST

AST stands for `Abstract Syntax Trees` which means you can read Python code, any block you wish, iterate and process.
Combine this with [`astpretty`](https://github.com/asottile/astpretty) and you have a powerful tool to understand the Python code.

My process developing this linter was:

1. Creating some sample Python code with a violation I would like to help with;
2. Running `astpretty` on the sample file to understand what I need to check;
3. Coding the analyzer logic;

```py
# Output from: astpretty --no except_bare.py
Module(
    body=[
        Expr(
            value=Constant(value="\nViolation:\n\nDon't use bare except\n", kind=None),
        ),
        FunctionDef(
            name='func',
            args=arguments(posonlyargs=[], args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
            body=[
                Try(
                    body=[
                        Assign(
                            targets=[Name(id='a', ctx=Store())],
                            value=Constant(value=1, kind=None),
                            type_comment=None,
                        ),
                    ],
                    handlers=[
                        ExceptHandler(
                            type=None,
                            name=None,
                            body=[Raise(exc=None, cause=None)],
                        ),
                    ],
                    orelse=[],
                    finalbody=[],
                ),
            ],
            decorator_list=[],
            returns=None,
            type_comment=None,
        ),
    ],
    type_ignores=[],
)
```

### Visiting Nodes

I relied on `ast.NodeVisitor` class to analyze my code.
The behavior is simple, straightforward and helps you to dive into specific statements when they happen.

I just need to inherit from this class, define a method named `visit_[STATEMENT_HERE](self, node)` and we're good to start coding.

Take for example the analyzer to avoid verbose reraises.

The goals is to avoid people from writing:

```py
try:
    ...
except Exception as ex:
    raise ex  # <-- This is verbose
```

So they can write it like:

```py
try:
    ...
except Exception:
    raise
```

For such case, by checking `astpretty` I learned that I want to visit `ExceptHandler` objects. [Check the final analyzer code](https://github.com/guilatrova/tryceratops/blob/56dbdf8/src/tryceratops/analyzers/exception_block.py#L24-L41):

```py
class ExceptVerboseReraiseAnalyzer(BaseAnalyzer, ast.NodeVisitor):  # <-- Inherit from ast.NodeVisitor
    violation_code = codes.VERBOSE_RERAISE

    @visit_error_handler
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:  # <-- We only want "except" blocks
        def is_raise_with_name(stm: ast.stmt, name: str):
            if isinstance(stm, ast.Raise) and isinstance(stm.exc, ast.Name):
                return stm.exc.id == name
            return False

        # If no name is set, then it's impossible to be verbose
        # since you don't have the object
        if node.name:
            for child in ast.walk(node):  # <-- We iterate over all children in that node
                if is_raise_with_name(child, node.name):  # <-- If condition is true, we found a violation
                    self._mark_violation(child)

        self.generic_visit(node)
```

### Capturing Comments in Python with `tokenize`

I never desired to enforce all linter rules on the developer, I like flexibility and, well, the code is yours. I wanted to allow developers to disable rules by settings comments like: `# notc: CODE`.

After gathering all violations in code using `ast`, I thought it would be very easy to capture such comments.
Turns out that `ast` does not handle comments, afterall, comments are not really python code.

I had then to use another lib `tokenize` to do that. This was more boring, because I had to read line by line and filter any comments that matches a regex:

```py
def parse_ignore_comments(content: TextIOWrapper) -> Generator[IgnoreViolation, None, None]:
    for toktype, tokval, start, *_ in tokenize.generate_tokens(content.readline):
        if toktype == tokenize.COMMENT:
            if match := re.search(IGNORE_TOKEN_PATT, tokval):
                yield _build_ignore_line(match, start)
```

Then I ended up with a tuple of: filename, parsed ast, list of comments.

### Testing scenarios with Pytest

Another cool challenge was: how to write tests?
There's a directory `tests/samples` for python files that intentionally violates specific rules.

The testing got very simple once I defined 2 helper functions: `read_sample` and `assert_violation`

```py
def read_sample(filename: str) -> ast.AST:
    ref_dir = f"{os.path.dirname(__file__)}/samples/violations/"
    path = f"{ref_dir}{filename}.py"

    with open(path) as sample:
        content = sample.read()
        loaded = ast.parse(content)
        return loaded


def assert_violation(code: str, msg: str, line: int, col: int, violation: Violation):
    assert violation.line == line
    assert violation.col == col
    assert violation.code == code
    assert violation.description == msg
```

Testing violations got very simple, I don't need to mock anything.

```py
def test_verbose_reraise():
    tree = read_sample("except_verbose_reraise")
    analyzer = analyzers.ExceptVerboseReraiseAnalyzer()
    code, msg = codes.VERBOSE_RERAISE

    assert_verbose = partial(assert_violation, code, msg)  # <-- I'm lazy, make function shorter

    violations = analyzer.check(tree, "filename")  # <-- Run analyzer
    assert len(violations) == 2
    first, second = violations

    assert_verbose(20, 8, first)  # <-- assert line, offset, expected violation
    assert_verbose(28, 12, second)  # <-- assert line, offset, expected violation
```

After getting the first analyzer passing, I started following a full TDD approach.
It's hard to test such stuff manually, so writing unit tests before code makes it easier to progress.

## CLI and Configs

Once the analyzers were set I needed to make it usable, and from your CLI.

### Using `click` as Python CLI

### Reading `pyproject.toml`

## Publishing Package to Pypi with Flit


### Credits

Thanks to God for the inspiration 🙌 ☁️ ☀️

Logo icon was made by [https://www.freepik.com](Freepik)

The [black](https://github.com/psf/black) project for insights.
