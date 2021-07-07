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

Once the analyzers were set (and somewhat working) I needed to make it usable, and linters fit well as a command line interface, so you can run it like: `tryceratops file.py` or maybe `tryceratops pydir`.

### Using `click` as Python CLI

[Click](https://click.palletsprojects.com/) is a simple framework to wrap your python code around a CLI quick. It's as simple as wrapping your function with a few decorators, see:

```py
EXPERIMENTAL_FLAG_OPTION = dict(is_flag=True, help="Whether to enable experimental analyzers.")
IGNORE_OPTION = dict(
    multiple=True,
    help="A violation to be ignored. e.g. -i TC200 -i TC201",
    type=click.Choice(CODE_CHOICES),
)
EXCLUDE_OPTION = dict(multiple=True, help="A dir to be excluded. e.g. -x tests/ -x fixtures/")

@click.command()
@click.argument("dir", nargs=-1)
@click.option("--experimental", **EXPERIMENTAL_FLAG_OPTION)
@click.option("-i", "--ignore", **IGNORE_OPTION)
@click.option("-x", "--exclude", **EXCLUDE_OPTION)
@click.version_option(tryceratops.__version__)
def entrypoint(dir: Tuple[str], experimental: bool, ignore: Tuple[str, ...], exclude: Tuple[str, ...]):
    ...

def main():
    logging.config.dictConfig(LOGGING_CONFIG)
    entrypoint()


if __name__ == "__main__":
    main()
```

Once I set some decorators like `@click.option` I had to receive and manage specific arguments which reflects the options I defined.
It's indeed simple. The annoying part was to figure out how to use some options (The documentation is not clear).

It took me a while to find out:

- `is_flag` can be used instead of some boolean option.
- if you want to allow multiple arguments you have to set different attributes. `nargs=-1` for the main argument and `multiple=True` for options. Not intuitive.

### Supporting `pre-commit`

I love [`pre-commit`](https://pre-commit.com/), it ensures that I'm not commiting some sort of code that will be a problem on CI and some other small improvements like end of line and trailing whitespace. I wanted to promote the same feature for devs to benefit from this as well, so now Tryceratops supports it.

It's indeed very simple, I just had to create a file named: [`pre-commit-hooks.yaml`](https://github.com/guilatrova/tryceratops/blob/main/.pre-commit-hooks.yaml) with the following:

```yaml
-   id: tryceratops
    name: tryceratops
    description: "Manage your exceptions in Python like a PRO"
    entry: tryceratops
    language: python
    language_version: python3
    types: [python]
    require_serial: true
```

Easy! Now anyone can add a new pre-commit hook in their repo like:

```yaml
  - repo: https://github.com/guilatrova/tryceratops
    rev: v0.2.3
    hooks:
      - id: tryceratops
```

### Supporting `pyproject.toml`

The next step would be to support [PEP518](https://www.python.org/dev/peps/pep-0518/) by allowing configs to be defined at the project level.
Maybe you don't like some violation that I set, that's fine, it shouldn't become a problem.

The goal is to support configs that someone would usually pass through CLI like:

```toml
[tool.tryceratops]
exclude = ["samples"]
ignore = ["TC002", "TC200", "TC300"]
experimental = true
```

Reading it was quite easy, there's a lib named `toml` that, guess what, reads and generates toml files.

```py
import toml

...

def load_config(dir: Sequence[str]) -> Optional[PyprojectConfig]:
    toml_file = find_pyproject_toml(dir)

    if toml_file:
        config = toml.load(toml_file)
        return config.get("tool", {}).get("tryceratops", {})
```

The actual challenge would be to find out whether a `pyproject.toml` file exists or not.
To be honest I wasn't sure on the best way to do it. Someone can run `tryceratops` from anywhere in the directory tree and it should always work! So I can't infer that the CLI is always being invoked from the root. Instead of struggling to find a solution myself (that probably would be bad), I decided to find out what other projects are doing. For instance, I checked on [`black`](https://github.com/psf/black) and adjusted it (by simplifying) to fit my needs, that's what I ended up with:

```py
def find_project_root(srcs: Sequence[str]) -> Path:
    """Return a directory containing .git, .hg, or pyproject.toml.

    That directory will be a common parent of all files and directories
    passed in `srcs`.

    If no directory in the tree contains a marker that would specify it's the
    project root, the root of the file system is returned.
    """
    if not srcs:
        srcs = [str(Path.cwd().resolve())]

    path_srcs = [Path(Path.cwd(), src).resolve() for src in srcs]

    # A list of lists of parents for each 'src'. 'src' is included as a
    # "parent" of itself if it is a directory
    src_parents = [list(path.parents) + ([path] if path.is_dir() else []) for path in path_srcs]

    common_base = max(
        set.intersection(*(set(parents) for parents in src_parents)),
        key=lambda path: path.parts,
    )

    for directory in (common_base, *common_base.parents):
        if (directory / ".git").exists():
            return directory

        if (directory / ".hg").is_dir():
            return directory

        if (directory / "pyproject.toml").is_file():
            return directory

    return directory


def find_pyproject_toml(path_search_start: Tuple[str, ...]) -> Optional[str]:
    """Find the absolute filepath to a pyproject.toml if it exists"""
    path_project_root = find_project_root(path_search_start)
    path_pyproject_toml = path_project_root / "pyproject.toml"
    if path_pyproject_toml.is_file():
        return str(path_pyproject_toml)
```

It's a very great idea to check on `.git` or `pyproject.toml` itself to decide whether it's the project root and, obviously, if worked just fine.

## Publishing Package to Pypi with Flit


## What's still missing?


### Credits

Thanks to God for the inspiration 🙌 ☁️ ☀️

Logo icon was made by [https://www.freepik.com](Freepik)

The [black](https://github.com/psf/black) project for insights.
