# Project Guidelines

## Test Rules
1. Every test should be marked by one of web, buttons, analysis, db, integration:
@pytest.mark.web — page load / HTML structure.
@pytest.mark.buttons — button endpoints & busy-state behavior.
@pytest.mark.analysis — labels and percentage formatting.
@pytest.mark.db — database schema/inserts/selects.
@pytest.mark.integration — end-to-end flows.

2. Use dependency injection so tests can pass fake scraper/loader/query functions without
hitting the network.
3. Use BeautifulSoup (or similar) for HTML assertions and a regex for two-decimal
percentages.
4. Shall not ship any test that depends on live internet or long-running scrapes.
5. Shall not use arbitrary sleep() for busy-state checks (make state observable/injectable).
6. Shall not leave any test unmarked (policy requires marks).
7. Shall not hard-code secrets, credentials, or environment-specific paths in code or tests.
8. Shall not require manual UI interaction for tests (no browser clicking; use Flask test
client).
9. 

## Documentation

1. Always update **module_4/README.md** when new features, functions, or CLI commands are added.  
   - Include: purpose, usage examples, and input/output description.  
   - Remove outdated references.

2. Whenever modifying files in **module_4/src**, maintain a clear record of changes:  
   - Inline code comments for non-trivial logic.  
   - Update or append to **module_4/CHANGELOG.md** with a brief summary of changes.  
