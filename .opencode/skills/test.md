# Test Skill

This skill provides quick commands for running tests in the BD Library Manager project.

## Commands

### Run all tests
```
/test
```
Runs the full test suite using pytest.

### Run tests with coverage
```
/test --coverage
```
Runs tests with coverage reporting.

### Run specific test module
```
/test <module>
```
Runs tests from a specific module (e.g., `/test test_comicinfo`).

### Run tests in verbose mode
```
/test --verbose
```
Runs tests with verbose output.

### Run failed tests first
```
/test --lf
```
Runs last failed tests first.

## Examples

- `/test` - Run all tests
- `/test test_comicinfo` - Run only comicinfo tests
- `/test --verbose` - Run all tests with verbose output
- `/test --coverage` - Run tests with coverage