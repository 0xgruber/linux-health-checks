# Tasks: Add User Configuration File Support

## 1. Configuration Loading Implementation
- [x] 1.1 Create configuration loading function using Python's `configparser` module
- [x] 1.2 Implement function to read from `health_check.cfg` in script directory
- [x] 1.3 Add error handling for missing config file (use defaults)
- [x] 1.4 Add error handling for malformed INI syntax (log warning, use defaults)
- [x] 1.5 Add error handling for missing sections/keys (use defaults for missing values)
- [x] 1.6 Log which config source is being used (config file vs defaults)

## 2. Configuration Example File
- [x] 2.1 Create `health_check.cfg.example` with all configurable values
- [x] 2.2 Organize config into logical sections: [output], [email], [smtp], [gpg], [thresholds], [version_check]
- [x] 2.3 Document each setting with inline comments
- [x] 2.4 Include valid value ranges and types for each setting
- [x] 2.5 Add security notes for sensitive settings (SMTP passwords, etc.)
- [x] 2.6 Include usage examples and common scenarios

## 3. Git Integration
- [x] 3.1 Add `health_check.cfg` to `.gitignore`
- [x] 3.2 Ensure `health_check.cfg.example` is tracked by git
- [x] 3.3 Test that user config is not overwritten by git pull

## 4. Configuration Helper Function
- [x] 4.1 Create `_cfg(section, key, default, value_type)` helper function
- [x] 4.2 Implement priority system: Environment Variable > Config File > Default
- [x] 4.3 Add type conversion for bool, int, float, str
- [x] 4.4 Add error handling for type conversion failures
- [x] 4.5 Return default value on any error

## 5. Environment Variable Support
- [x] 5.1 Check environment variables before config file
- [x] 5.2 Use uppercase env var names (e.g., OUTPUT_DIR for output.output_dir)
- [x] 5.3 Convert env var string values to appropriate types
- [x] 5.4 Log when environment variable override is used

## 6. Validation
- [x] 6.1 Validate threshold percentages are 0-100
- [x] 6.2 Validate integer values are within acceptable ranges
- [x] 6.3 Warn about unknown config sections or keys
- [x] 6.4 Provide helpful error messages for invalid values
- [x] 6.5 Fall back to defaults for invalid values

## 7. Security
- [x] 7.1 Check config file permissions using os.stat()
- [x] 7.2 Warn if file is readable by group or others (mode & 0o044)
- [x] 7.3 Recommend chmod 600 for files with sensitive data
- [x] 7.4 Continue execution even with insecure permissions (with warning)

## 8. Update Configuration Section
- [x] 8.1 Update CONFIGURATION comment block to reference config file
- [x] 8.2 Replace all hardcoded values with `_cfg()` calls
- [x] 8.3 Maintain backward compatibility (defaults match old values)
- [x] 8.4 Update OUTPUT_DIR calculation
- [x] 8.5 Update EMAIL_* settings
- [x] 8.6 Update SMTP_* settings
- [x] 8.7 Update GPG_* settings
- [x] 8.8 Update threshold settings (FILESYSTEM_*, MEMORY_*, LOAD_*)
- [x] 8.9 Update version check settings

## 9. Documentation
- [x] 9.1 Add configuration section to README.md
- [x] 9.2 Document configuration priority system
- [x] 9.3 Add examples of common config scenarios
- [x] 9.4 Add security best practices section
- [x] 9.5 Update version badges in README
- [x] 9.6 Add link to config example file

## 10. Testing
- [x] 10.1 Test with no config file (uses defaults)
- [x] 10.2 Test with complete config file (all values)
- [x] 10.3 Test with partial config file (some values missing)
- [x] 10.4 Test with malformed INI syntax
- [x] 10.5 Test with invalid value types
- [x] 10.6 Test with invalid threshold ranges
- [x] 10.7 Test environment variable overrides
- [x] 10.8 Test file permission warnings
- [x] 10.9 Test config file discovery from different working directories
- [x] 10.10 Run full script with config to ensure no breaking changes
