# kspyder — Technical Debt & Known Flaws

## Legend
- ✅ Fixed
- 🔴 Bug / runtime error
- 🟠 Architecture / design
- 🟡 Code quality
- 🔵 Configuration / security

---

## 1. Module loading & import system ✅
**Fixed.** Connectors are now proper Python packages under `Connectors/<name>/`.
`sys.path` manipulation reduced to one entry (`ROOT_FOLDER`). `MODULES_MAP` and its
`baseconfig.yml` block removed. `clientHandler` dynamically loads connectors via
`import_module("Connectors.<source>")` without any static registry.

---

## 2. Abstract interface methods silently do nothing 🔴
**Files:** [Engines/rpcExtractorEngine.py](Engines/rpcExtractorEngine.py#L16-L23)

`get_count()`, `read_query()`, and `forge_item()` on `GenericRPCExtractor` create
`ValueError` objects but never raise them. Any subclass that forgets to override one of
these will silently return `None` instead of erroring, making bugs very hard to trace.

```python
def get_count(self, **kwargs):
    ValueError("...")   # bug: should be `raise ValueError(...)`
```

**Fix:** Use `raise NotImplementedError(...)` or make `GenericRPCExtractor` an ABC with
`@abstractmethod`.

---

## 3. Invalid datetime API call 🔴
**File:** [Engines/rpcExtractorEngine.py:30](Engines/rpcExtractorEngine.py#L30)

```python
now = datetime.datetime.now(datetime.datetime.utc)  # AttributeError at runtime
```

`datetime.datetime` has no `.utc` attribute. Should be `datetime.timezone.utc`.

---

## 4. `print()` statements in engine code 🟡
**Files:** [Engines/rpcExtractorEngine.py:130](Engines/rpcExtractorEngine.py#L130),
[main.py:182](main.py#L182)

`print("{} more to go.".format(batch_size))` fires on every pagination batch.
`print(params)` fires on every CLI invocation. Both should go through the logger.

---

## 5. No interface contract for connectors 🟠
**Files:** [Engines/restExtractorEngine.py](Engines/restExtractorEngine.py),
[Engines/rpcExtractorEngine.py](Engines/rpcExtractorEngine.py)

There is no ABC or protocol defining what a connector must implement. The base classes
set placeholder string attributes in `__init__` instead of enforcing subclass contracts:

```python
self.client = "This is an empty client from the GenericRPCExtractor interface..."
```

This means a misconfigured subclass will pass `isinstance` checks and only blow up at
query time with an unhelpful `AttributeError` on a string object.

---

## 6. `clientHandler` has inconsistent instantiation logic 🟠
**File:** [common/clientHandler.py](common/clientHandler.py)

`get_client()` checks for a profile file and calls `from_profile()` if it exists, or
falls back to `client_class(**kwargs)` otherwise. The problem is that not all connectors
implement `from_profile()`, and those that do have different signatures. This creates a
fragile implicit contract: whether instantiation works depends on which files happen to
be present in the conf folder at runtime.

---

## 7. Stub credentials in source code 🔵
**File:** [common/config.py:37-47](common/config.py#L37-L47)

```python
PLACEHOLDER_PROFILE = {
    'dbname': 'stub',
    'username': 'stub_user',
    'password': 'blah'
}
ODOO_PROFILE = PLACEHOLDER_PROFILE
PS_PROFILE = PLACEHOLDER_PROFILE
AZURE_PROFILE = PLACEHOLDER_PROFILE
```

These are referenced directly as default argument values in connector constructors,
meaning any connector instantiated without a profile will silently use these stub
credentials rather than failing loudly. The `# TODO get rid of this with KWI-30`
comment indicates this is a known issue.

---

## 8. Global module-level state in `config.py` 🟠
**File:** [common/config.py](common/config.py)

All config values (`PAGE_SIZE`, `DUMP_JSON`, `BASE_FILE_HANDLER`, etc.) are instantiated
at import time. Consequences:
- `KSPYDER_CONF` env var must be set before the first import; an unset or wrong value
  silently constructs a bad `CONF_FOLDER` path and fails late with an obscure
  `FileNotFoundError`.
- Impossible to run tests with a different config without reloading the module.
- Logger is also initialized at import time via `loggingHandler`, making log level
  reconfiguration per-run difficult.

---

## 9. `main.py` dispatches via `locals()` 🟠
**File:** [main.py:184-185](main.py#L184-L185)

```python
function = locals()[args.operation]
function()
```

Calling arbitrary local functions by name from user input is an anti-pattern:
it's not statically analysable, any function in scope is callable (including helpers),
and it gives no useful error message when an invalid operation is passed.
A simple `dispatch = {'extract': extract, 'pipelines': pipelines, ...}` dict would
be safer and clearer.

---

## 10. `pipelineEngine` is a kitchen sink 🟠
**File:** [Engines/pipelineEngine.py](Engines/pipelineEngine.py)

The class mixes pipeline orchestration (`execute_pipeline`) with generic data
transformation utilities (`apply_filters`, `get_unique_key_list`, `set_static_data`)
and a MongoDB shortcut (`get_data_to_mongo`). The transformation utilities exist only
because pipeline YAML steps can reference `pipelineEngine` as the worker. This creates
a growing grab-bag of methods over time rather than a clean orchestration layer.

---

## 11. MongoDB connector hardcodes localhost with no auth 🔵
**File:** [Connectors/mongoDB/connector.py](Connectors/mongoDB/connector.py)

The default `MongoClient` initialization uses `localhost:27017` with no credentials.
There is no environment variable override or profile-based connection string for the
MongoDB host, making it impossible to point the connector at a remote or
authenticated instance without modifying the source.

---

## 12. No config or YAML schema validation 🟠
**Files:** [common/profileHandler.py](common/profileHandler.py),
[common/fileHandler.py](common/fileHandler.py)

YAML files are loaded and accessed by key without any structural validation. A missing
key or wrong type in a profile or models YAML raises a bare `KeyError` or `TypeError`
deep inside engine code, with no indication of which file is malformed or what was
expected.

---

## 13. Duplicate `get_data()` logic across engine base classes 🟡
**Files:** [Engines/restExtractorEngine.py](Engines/restExtractorEngine.py),
[Engines/rpcExtractorEngine.py](Engines/rpcExtractorEngine.py)

Both engines implement nearly identical `get_data()` methods (pagination loop, input
merging, error collection, JSON dump). The duplication means any fix or change must be
applied twice and can drift over time. A shared base class or mixin would eliminate this.

---

## 14. Mutable default arguments 🟡
**Files:** Throughout connectors and engines

Many methods use mutable default arguments:
```python
def get_data(self, search_domains=[], input_data=[{}], **params):
```
Python evaluates default values once at function definition time, so mutations to these
defaults persist across calls. This is a classic Python footgun.

---

## 15. Commented-out code blocks 🟡
**Files:** [Engines/pipelineEngine.py:145-156](Engines/pipelineEngine.py#L145-L156),
[main.py](main.py), [Engines/restExtractorEngine.py](Engines/restExtractorEngine.py),
and others

Large commented-out code sections add noise and obscure intent. Version history in git
is the right place for this; dead code should be deleted.

---

## 16. No type hints 🟡
**Files:** All

The codebase has no type annotations. Combined with the heavy use of `**kwargs` and
`**params`, static analysis tools (mypy, pyright) cannot catch type errors, and IDE
autocompletion is limited. The internal dataset format (`{'header': {...}, 'data': [...]}`)
is an implicit contract that is never documented or enforced.
